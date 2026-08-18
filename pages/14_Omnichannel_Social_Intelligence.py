import os

import pandas as pd
import plotly.graph_objects as go
import streamlit as st

from utils.entity_selector import get_entity, get_entity_query
from utils.global_i18n import get_language
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

@st.cache_data(ttl=1800, show_spinner=False)
def load_social(query, selected_platforms, youtube_api_key, limit_per_platform):
    return collect_expanded_social_narratives(
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

st.title("🌐 Omnichannel Social Intelligence")
st.caption(
    "Cross-platform narrative comparison for public "
    "and approved social data sources."
)

c1, c2, c3, c4 = st.columns(4)
c1.metric("Entity", display_name)
c2.metric("Country", entity["Country"])
c3.metric("Sector", entity["Sector"])
c4.metric("Priority", entity["Priority"])

st.sidebar.markdown("### Platform Controls")

platform_options = list(EXPANDED_PLATFORM_CATALOG.keys())

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

aliases_text = st.sidebar.text_input(
    "Additional multilingual aliases",
    value="",
    help=(
        "Optional comma-separated local names. "
        "For example, add Arabic, Russian, French, "
        "Spanish, or German versions of the entity name."
    ),
)

limit_per_platform = st.sidebar.slider(
    "Maximum rows per live source",
    min_value=5,
    max_value=50,
    value=20,
    step=5,
)

if st.sidebar.button("Refresh social data"):
    load_social.clear()

queries = [query]
queries.extend(
    alias.strip()
    for alias in aliases_text.split(",")
    if alias.strip()
)

frames = []
coverage_frames = []
errors = []

for current_query in dict.fromkeys(queries):
    posts_part, coverage_part, errors_part = load_social(
        current_query,
        tuple(selected_platforms),
        youtube_api_key,
        limit_per_platform,
    )

    if not posts_part.empty:
        posts_part = posts_part.copy()
        posts_part["Search Query Used"] = current_query
        frames.append(posts_part)

    if not coverage_part.empty:
        coverage_frames.append(coverage_part)

    errors.extend(errors_part)

if frames:
    posts = pd.concat(frames, ignore_index=True)
    posts = posts.drop_duplicates(
        subset=["Platform", "Title", "Url"],
        keep="first",
    )
else:
    posts = pd.DataFrame()

if coverage_frames:
    coverage = pd.concat(coverage_frames, ignore_index=True)
    coverage = (
        coverage.groupby(
            [
                "Platform",
                "Source Type",
                "Access Mode",
                "Geographic Coverage",
                "Language Coverage",
            ],
            dropna=False,
        )
        .agg(
            **{
                "Rows": ("Rows", "sum"),
                "Data Status": (
                    "Data Status",
                    lambda values: " | ".join(
                        sorted(set(map(str, values)))
                    ),
                ),
            }
        )
        .reset_index()
    )
else:
    coverage = pd.DataFrame()

st.subheader("Source Coverage & Connector Readiness")
st.dataframe(coverage, use_container_width=True, hide_index=True)

if errors:
    with st.expander("Source connection notes"):
        for error in sorted(set(errors)):
            st.write(error)

if posts.empty:
    st.warning(
        "No live public rows were returned. "
        "Some platforms require official API access."
    )
    st.stop()

available_languages = sorted(
    value
    for value in posts["Language"].dropna().astype(str).unique()
    if value and value.lower() != "unknown"
)

content_language = st.sidebar.selectbox(
    "Content language filter",
    ["All languages"] + available_languages,
)

filtered_posts = posts.copy()

if content_language != "All languages":
    filtered_posts = filtered_posts[
        filtered_posts["Language"].astype(str).str.contains(
            content_language,
            case=False,
            na=False,
        )
    ]

comparison = platform_comparison(filtered_posts)

st.subheader("Cross-Platform Executive Overview")

k1, k2, k3, k4 = st.columns(4)
k1.metric("Live Mentions", int(len(filtered_posts)))
k2.metric("Connected Platforms", int(filtered_posts["Platform"].nunique()))
k3.metric("Total Engagement", int(filtered_posts["Engagement"].fillna(0).sum()))
k4.metric(
    "Languages Observed",
    int(
        filtered_posts["Language"]
        .replace("unknown", pd.NA)
        .dropna()
        .nunique()
    ),
)

st.subheader("Platform Risk Comparison")
st.dataframe(comparison, use_container_width=True, hide_index=True)

if not comparison.empty:
    risk_chart = go.Figure(
        go.Bar(
            x=comparison["Platform"],
            y=comparison["Platform Risk"],
            text=comparison["Platform Risk"],
            textposition="auto",
        )
    )
    risk_chart.update_layout(
        height=450,
        yaxis_title="Platform Risk",
        yaxis_range=[0, 100],
    )
    st.plotly_chart(risk_chart, use_container_width=True)

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
    st.plotly_chart(volume_chart, use_container_width=True)

with right:
    sentiment_chart = go.Figure(
        go.Scatter(
            x=comparison["Average Sentiment"],
            y=comparison["Negative Share %"],
            mode="markers+text",
            text=comparison["Platform"],
            textposition="top center",
            marker={
                "size": comparison["Mention Share %"].clip(lower=4) * 1.5
            },
        )
    )
    sentiment_chart.update_layout(
        title="Narrative Pressure Map",
        xaxis_title="Average Sentiment (-1 to +1)",
        yaxis_title="Negative Share %",
        height=430,
    )
    st.plotly_chart(sentiment_chart, use_container_width=True)

st.subheader("Cross-Platform Narrative Overlap")

overlap = cross_platform_terms(filtered_posts, top_n=20)

if overlap.empty:
    st.info(
        "No recurring terms appeared on multiple live platforms in this run."
    )
else:
    st.dataframe(overlap, use_container_width=True, hide_index=True)

st.subheader("High-Risk Social Narratives")

risk_posts = filtered_posts.copy()
risk_posts["Risk Signal"] = (
    (1 - risk_posts["Sentiment"]) * 35
    + risk_posts["Engagement"]
    .fillna(0)
    .rank(pct=True, method="average")
    * 30
).clip(0, 100)

display_columns = [
    "Platform",
    "Title",
    "Author",
    "Published_At",
    "Engagement",
    "Sentiment",
    "Sentiment_Label",
    "Language",
    "Search Query Used",
    "Risk Signal",
    "Url",
]

st.dataframe(
    risk_posts
    .sort_values("Risk Signal", ascending=False)[display_columns]
    .head(50),
    use_container_width=True,
    hide_index=True,
)

if get_language() != "en":
    st.warning(
        "Non-English social sentiment should be treated as exploratory "
        "until a validated multilingual sentiment model is connected. "
        "Content collection and cross-platform comparison remain available."
    )
