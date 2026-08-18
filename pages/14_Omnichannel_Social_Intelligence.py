import os

import pandas as pd
import plotly.graph_objects as go
import streamlit as st

from utils.entity_selector import get_entity, get_entity_query
from utils.social_expansion import (
    EXPANDED_PLATFORM_CATALOG,
    collect_expanded_social_narratives,
    cross_platform_terms,
    platform_comparison,
)


st.set_page_config(
    page_title="Omnichannel Social Intelligence",
    page_icon="🌐",
    layout="wide",
)


def get_secret_value(name):
    try:
        value = st.secrets.get(name, "")
    except Exception:
        value = ""

    return value or os.environ.get(name, "")


@st.cache_data(
    ttl=1800,
    show_spinner=False,
)
def load_social(
    query,
    selected_platforms,
    youtube_api_key,
    limit_per_platform,
):
    return collect_expanded_social_narratives(
        query=query,
        selected_platforms=list(
            selected_platforms
        ),
        youtube_api_key=youtube_api_key,
        limit_per_platform=limit_per_platform,
    )


entity = get_entity()
display_name = entity["Short_Name"]
youtube_query = get_entity_query(
    entity,
    "YouTube_Query",
)
search_query = get_entity_query(
    entity,
    "Search_Query",
)
default_query = (
    youtube_query
    or search_query
    or display_name
)

youtube_api_key = get_secret_value(
    "YOUTUBE_API_KEY"
)

st.title(
    "🌐 Omnichannel Social Intelligence"
)

st.caption(
    "Cross-platform narrative comparison for public "
    "and approved social data sources."
)

c1, c2, c3, c4 = st.columns(4)
c1.metric("Entity", display_name)
c2.metric("Country", entity["Country"])
c3.metric("Sector", entity["Sector"])
c4.metric("Priority", entity["Priority"])

st.sidebar.markdown(
    "### Platform Controls"
)

platform_options = list(
    EXPANDED_PLATFORM_CATALOG.keys()
)

default_platforms = [
    "YouTube",
    "Reddit",
    "Hacker News",
    "Mastodon / Fediverse",
    "Bluesky",
]

selected_platforms = st.sidebar.multiselect(
    "Platforms",
    platform_options,
    default=[
        platform
        for platform in default_platforms
        if platform in platform_options
    ],
)

query = st.sidebar.text_input(
    "Narrative query",
    value=default_query,
)

limit_per_platform = st.sidebar.slider(
    "Maximum rows per live source",
    min_value=5,
    max_value=50,
    value=20,
    step=5,
)

if st.sidebar.button(
    "Refresh social data"
):
    load_social.clear()

posts, coverage, errors = load_social(
    query,
    tuple(selected_platforms),
    youtube_api_key,
    limit_per_platform,
)

comparison = platform_comparison(
    posts
)

st.subheader(
    "Source Coverage & Connector Readiness"
)

st.dataframe(
    coverage,
    use_container_width=True,
    hide_index=True,
)

if errors:
    with st.expander(
        "Source connection notes"
    ):
        for error in errors:
            st.write(error)

if posts.empty:
    st.warning(
        "No live public rows were returned. "
        "Some platforms require official API access."
    )
    st.stop()

st.subheader(
    "Cross-Platform Executive Overview"
)

k1, k2, k3, k4 = st.columns(4)

k1.metric(
    "Live Mentions",
    int(len(posts)),
)
k2.metric(
    "Connected Platforms",
    int(
        posts["Platform"].nunique()
    ),
)
k3.metric(
    "Total Engagement",
    int(
        posts["Engagement"]
        .fillna(0)
        .sum()
    ),
)
k4.metric(
    "Languages Observed",
    int(
        posts["Language"]
        .replace("unknown", pd.NA)
        .dropna()
        .nunique()
    ),
)

st.subheader(
    "Platform Risk Comparison"
)

st.dataframe(
    comparison,
    use_container_width=True,
    hide_index=True,
)

if not comparison.empty:
    risk_chart = go.Figure(
        go.Bar(
            x=comparison["Platform"],
            y=comparison["Platform Risk"],
            text=comparison[
                "Platform Risk"
            ],
            textposition="auto",
        )
    )
    risk_chart.update_layout(
        height=450,
        yaxis_title="Platform Risk",
        yaxis_range=[0, 100],
    )
    st.plotly_chart(
        risk_chart,
        use_container_width=True,
    )

left, right = st.columns(2)

with left:
    volume_chart = go.Figure()

    volume_chart.add_trace(
        go.Bar(
            x=comparison["Platform"],
            y=comparison["Mentions"],
            name="Mentions",
        )
    )
    volume_chart.add_trace(
        go.Bar(
            x=comparison["Platform"],
            y=comparison["Engagement"],
            name="Engagement",
        )
    )
    volume_chart.update_layout(
        title="Volume & Engagement",
        barmode="group",
        height=430,
    )
    st.plotly_chart(
        volume_chart,
        use_container_width=True,
    )

with right:
    sentiment_chart = go.Figure(
        go.Scatter(
            x=comparison[
                "Average Sentiment"
            ],
            y=comparison[
                "Negative Share %"
            ],
            mode="markers+text",
            text=comparison["Platform"],
            textposition="top center",
            marker={
                "size": (
                    comparison[
                        "Mention Share %"
                    ]
                    .clip(lower=4)
                    * 1.5
                )
            },
        )
    )
    sentiment_chart.update_layout(
        title="Narrative Pressure Map",
        xaxis_title=(
            "Average Sentiment "
            "(-1 to +1)"
        ),
        yaxis_title=(
            "Negative Share %"
        ),
        height=430,
    )
    st.plotly_chart(
        sentiment_chart,
        use_container_width=True,
    )

st.subheader(
    "Cross-Platform Narrative Overlap"
)

overlap = cross_platform_terms(
    posts,
    top_n=20,
)

if overlap.empty:
    st.info(
        "No recurring terms appeared on "
        "multiple live platforms in this run."
    )
else:
    st.dataframe(
        overlap,
        use_container_width=True,
        hide_index=True,
    )

    overlap_chart = go.Figure(
        go.Bar(
            x=overlap["Frequency"],
            y=overlap["Term"],
            orientation="h",
            text=overlap[
                "Platform Count"
            ],
        )
    )
    overlap_chart.update_layout(
        height=520,
        xaxis_title=(
            "Cross-platform frequency"
        ),
        yaxis={
            "categoryorder":
            "total ascending"
        },
    )
    st.plotly_chart(
        overlap_chart,
        use_container_width=True,
    )

st.subheader(
    "High-Risk Social Narratives"
)

risk_posts = posts.copy()

risk_posts["Risk Signal"] = (
    (1 - risk_posts["Sentiment"])
    * 35
    + risk_posts["Engagement"]
    .fillna(0)
    .rank(
        pct=True,
        method="average",
    )
    * 30
).clip(0, 100)

risk_posts = risk_posts.sort_values(
    "Risk Signal",
    ascending=False,
)

display_columns = [
    "Platform",
    "Title",
    "Author",
    "Published_At",
    "Engagement",
    "Sentiment",
    "Sentiment_Label",
    "Language",
    "Risk Signal",
    "Url",
]

st.dataframe(
    risk_posts[display_columns]
    .head(50),
    use_container_width=True,
    hide_index=True,
)

st.info(
    "Live public/API data and connector-ready "
    "sources are shown separately. Restricted "
    "platforms should only be connected through "
    "official or approved access."
)
