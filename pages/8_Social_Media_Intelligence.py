import os

import pandas as pd
import plotly.graph_objects as go
import streamlit as st

from utils.entity_selector import get_entity, get_entity_query
from utils.glossary import metric_help, render_glossary
from utils.social_utils import (
    PLATFORM_CATALOG,
    calculate_social_metrics,
    collect_social_narratives,
    extract_terms,
    summarize_platforms,
)

st.set_page_config(
    page_title="Social Media Intelligence",
    page_icon="SM",
    layout="wide",
)


def get_secret_value(name):
    try:
        value = st.secrets.get(name, "")
    except Exception:
        value = ""

    return value or os.environ.get(name, "")


@st.cache_data(ttl=1800, show_spinner=False)
def load_social_narratives(query, selected_platforms, youtube_api_key, limit_per_platform):
    return collect_social_narratives(
        query=query,
        selected_platforms=list(selected_platforms),
        youtube_api_key=youtube_api_key,
        limit_per_platform=limit_per_platform,
    )


entity = get_entity()

display_name = entity["Short_Name"]
youtube_query = get_entity_query(entity, "YouTube_Query")
search_query = get_entity_query(entity, "Search_Query")
default_query = youtube_query or search_query or display_name
youtube_api_key = get_secret_value("YOUTUBE_API_KEY")

st.title("Social Media Intelligence")

render_glossary(["SSI", "SVI", "NPI", "SRS", "RII", "NRRI", "OLI"])

st.markdown(f"""
### Monitoring Social Reputation Signals

**Selected Entity:** {display_name}

This module extends the dashboard beyond Google News by collecting social,
forum, video, and decentralized-network narratives where public or official
API access is available.
""")

c1, c2, c3, c4 = st.columns(4)
c1.metric("Type", entity["Entity_Type"])
c2.metric("Country", entity["Country"])
c3.metric("Sector", entity["Sector"])
c4.metric("Priority", entity["Priority"])

st.sidebar.markdown("### Social Source Controls")

platform_options = list(PLATFORM_CATALOG.keys())
default_platforms = [
    "Hacker News",
    "Mastodon / Fediverse",
    "Reddit",
    "YouTube",
]

selected_platforms = st.sidebar.multiselect(
    "Platforms",
    options=platform_options,
    default=default_platforms,
    help="Live rows are collected where public/API access is available. Connector-only platforms are shown in source coverage.",
)

query = st.sidebar.text_input(
    "Social query",
    value=default_query,
    help="Use the entity name, product name, campaign, AI system, or crisis keyword you want to monitor.",
)

limit_per_platform = st.sidebar.slider(
    "Maximum rows per live source",
    min_value=5,
    max_value=50,
    value=20,
    step=5,
)

if st.sidebar.button("Refresh social data"):
    load_social_narratives.clear()

posts, coverage, errors = load_social_narratives(
    query,
    tuple(selected_platforms),
    youtube_api_key,
    limit_per_platform,
)

metrics = calculate_social_metrics(posts)
platform_summary = summarize_platforms(posts)

st.divider()
st.subheader("Executive Overview")

k1, k2, k3, k4, k5 = st.columns(5)
k1.metric("SSI", metrics["SSI"], help=metric_help("SSI"))
k2.metric("SVI", metrics["SVI"], help=metric_help("SVI"))
k3.metric("NPI", metrics["NPI"], help=metric_help("NPI"))
k4.metric("SRS", metrics["SRS"], help=metric_help("SRS"))
k5.metric("Platforms", metrics["Platforms"], help="Number of selected platforms returning live narrative rows.")

if metrics["Mentions"] > 0:
    st.success(f"Current Social Risk Status: {metrics['Risk_Label']}")
else:
    st.info("No live social rows returned yet. Connect API credentials or broaden the query/platform selection.")

st.caption(
    "Social geography is source-level in this prototype. Reliable user-level geography requires official platform metadata, consent-aware collection, and platform terms compliance."
)

if errors:
    with st.expander("Source connection notes"):
        for error in errors:
            st.write(f"- {error}")

st.subheader("Source Coverage")
st.dataframe(
    coverage,
    use_container_width=True,
    hide_index=True,
)

if posts.empty:
    st.subheader("Connector Roadmap")
    st.info(
        "The dashboard is ready for multiple social media connectors. Add API keys or approved platform access for YouTube, X/Twitter, TikTok, Instagram, LinkedIn, Bluesky, and Reddit production collection."
    )
else:
    st.subheader("Platform Comparison")

    col1, col2 = st.columns(2)

    with col1:
        volume_chart = go.Figure()
        volume_chart.add_trace(
            go.Bar(
                x=platform_summary["Platform"],
                y=platform_summary["Mentions"],
                name="Mentions",
            )
        )
        volume_chart.add_trace(
            go.Bar(
                x=platform_summary["Platform"],
                y=platform_summary["Engagement"],
                name="Engagement",
            )
        )
        volume_chart.update_layout(
            barmode="group",
            height=420,
            xaxis_title="Platform",
            yaxis_title="Count",
            legend_title_text="Metric",
        )
        st.plotly_chart(volume_chart, use_container_width=True)

    with col2:
        sentiment_chart = go.Figure(
            go.Bar(
                x=platform_summary["Platform"],
                y=platform_summary["Average Sentiment"],
                marker_color=[
                    "#2E7D32" if value > 0.05 else "#C62828" if value < -0.05 else "#6B7280"
                    for value in platform_summary["Average Sentiment"]
                ],
            )
        )
        sentiment_chart.update_layout(
            height=420,
            xaxis_title="Platform",
            yaxis_title="Average sentiment (-1 to +1)",
            yaxis_range=[-1, 1],
        )
        st.plotly_chart(sentiment_chart, use_container_width=True)

    col3, col4 = st.columns(2)

    with col3:
        sentiment_counts = posts["Sentiment_Label"].value_counts().reset_index()
        sentiment_counts.columns = ["Sentiment", "Rows"]
        donut = go.Figure(
            data=[
                go.Pie(
                    labels=sentiment_counts["Sentiment"],
                    values=sentiment_counts["Rows"],
                    hole=0.58,
                )
            ]
        )
        donut.update_layout(height=380)
        st.subheader("Sentiment Mix")
        st.plotly_chart(donut, use_container_width=True)

    with col4:
        language_counts = posts["Language"].fillna("unknown").value_counts().reset_index()
        language_counts.columns = ["Language", "Rows"]
        language_chart = go.Figure(
            go.Bar(
                x=language_counts["Language"],
                y=language_counts["Rows"],
            )
        )
        language_chart.update_layout(
            height=380,
            xaxis_title="Language metadata",
            yaxis_title="Rows",
        )
        st.subheader("Language Signals")
        st.plotly_chart(language_chart, use_container_width=True)

    st.subheader("Platform Summary")
    st.dataframe(
        platform_summary,
        use_container_width=True,
        hide_index=True,
    )

    st.subheader("Trending Social Narratives")
    terms = extract_terms(posts)

    if terms.empty:
        st.info("No recurring narrative terms detected in the current social corpus.")
    else:
        terms_chart = go.Figure(
            go.Bar(
                x=terms["Frequency"],
                y=terms["Term"],
                orientation="h",
            )
        )
        terms_chart.update_layout(
            height=420,
            xaxis_title="Frequency",
            yaxis_title="Narrative term",
            yaxis={"categoryorder": "total ascending"},
        )
        st.plotly_chart(terms_chart, use_container_width=True)

    st.subheader("Narrative Records")
    record_columns = [
        "Platform",
        "Title",
        "Author",
        "Published_At",
        "Language",
        "Engagement",
        "Sentiment",
        "Sentiment_Label",
        "Geo_Scope",
        "Data_Status",
        "Url",
    ]
    st.dataframe(
        posts[record_columns],
        use_container_width=True,
        hide_index=True,
    )

st.subheader("Connector Readiness")

connector_rows = []

for platform, meta in PLATFORM_CATALOG.items():
    if "required" in meta["access_mode"].lower() or "connector" in meta["access_mode"].lower():
        connector_rows.append({
            "Platform": platform,
            "Connector Need": meta["access_mode"],
            "Research Value": meta["source_type"],
            "Governance Note": "Use official API or approved research access; avoid scraping restricted content.",
        })

st.dataframe(
    pd.DataFrame(connector_rows),
    use_container_width=True,
    hide_index=True,
)

st.subheader("Executive Insight")

st.info(f"""
{display_name} is now monitored across social and forum sources, not only Google News.

Current query: {query}

Live social rows: {metrics["Mentions"]}

Connected platforms with rows: {metrics["Platforms"]}

Current Social Risk Score: {metrics["SRS"]} ({metrics["Risk_Label"]})

For research, policy, and organizational decision-support use, this should be
presented as a prototype for multi-source narrative intelligence. The next
methodological step is to add official platform connectors and validated
multilingual sentiment models, so social narratives can be compared with Google
News narratives in a transparent and ethically governed way.
""")
