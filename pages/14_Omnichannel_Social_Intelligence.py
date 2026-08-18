import os

import pandas as pd
import plotly.graph_objects as go
import streamlit as st

from utils.entity_selector import get_entity, get_entity_query
from utils.multilingual_content import (
    CONTENT_LANGUAGES,
    NEWS_PROFILES,
    detect_script_language,
    get_selected_content_languages,
    resolve_query_alias,
    score_multilingual_sentiment,
    sentiment_label,
)
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

default_query = (
    get_entity_query(
        entity,
        "YouTube_Query",
    )
    or get_entity_query(
        entity,
        "Search_Query",
    )
    or display_name
)

youtube_api_key = get_secret_value(
    "YOUTUBE_API_KEY"
)

st.title(
    "🌐 Omnichannel Social Intelligence"
)

st.caption(
    "Cross-platform, multilingual narrative comparison "
    "for public and approved digital sources."
)

c1, c2, c3, c4 = st.columns(4)
c1.metric("Entity", display_name)
c2.metric("Country", entity["Country"])
c3.metric("Sector", entity["Sector"])
c4.metric("Priority", entity["Priority"])

platform_options = list(
    EXPANDED_PLATFORM_CATALOG.keys()
)

selected_platforms = st.sidebar.multiselect(
    "Platforms",
    platform_options,
    default=[
        "YouTube",
        "Reddit",
        "Hacker News",
        "Mastodon / Fediverse",
        "Bluesky",
    ],
)

base_query = st.sidebar.text_input(
    "Narrative query",
    value=default_query,
)

manual_aliases = st.sidebar.text_input(
    "Additional multilingual aliases",
    "",
)

limit_per_platform = st.sidebar.slider(
    "Maximum rows per live source",
    5,
    30,
    10,
    5,
)

content_languages = (
    get_selected_content_languages()
)

language_name_by_code = {
    code: name
    for name, code
    in CONTENT_LANGUAGES.items()
}

search_plan = [
    (
        code,
        resolve_query_alias(
            base_query,
            code,
        ),
    )
    for code
    in content_languages
]

for alias in manual_aliases.split(","):
    alias = alias.strip()
    if alias:
        search_plan.append(
            (
                "custom",
                alias,
            )
        )

unique_plan = []
seen = set()

for code, current_query in search_plan:
    key = current_query.lower()
    if key in seen:
        continue
    seen.add(key)
    unique_plan.append(
        (
            code,
            current_query,
        )
    )

if st.sidebar.button(
    "Refresh social data"
):
    load_social.clear()

frames = []
coverage_frames = []
errors = []

with st.spinner(
    "Collecting multilingual omnichannel narratives..."
):
    for code, current_query in unique_plan:
        posts_part, coverage_part, errors_part = (
            load_social(
                current_query,
                tuple(
                    selected_platforms
                ),
                youtube_api_key,
                limit_per_platform,
            )
        )

        if not posts_part.empty:
            posts_part = (
                posts_part.copy()
            )

            posts_part[
                "Search Query Used"
            ] = current_query

            posts_part[
                "Search Language"
            ] = (
                language_name_by_code.get(
                    code,
                    "Custom",
                )
            )

            language_codes = []

            for _, row in posts_part.iterrows():
                fallback = (
                    code
                    if code
                    in NEWS_PROFILES
                    else "en"
                )

                language_codes.append(
                    detect_script_language(
                        row.get(
                            "Text",
                            "",
                        ),
                        fallback,
                    )
                )

            posts_part[
                "Language Code"
            ] = language_codes

            posts_part[
                "Language"
            ] = [
                NEWS_PROFILES.get(
                    code_value,
                    {},
                ).get(
                    "label",
                    code_value,
                )
                for code_value
                in language_codes
            ]

            scores = []
            methods = []
            confidences = []

            for _, row in posts_part.iterrows():
                score, method, confidence = (
                    score_multilingual_sentiment(
                        row.get(
                            "Text",
                            "",
                        ),
                        row[
                            "Language Code"
                        ],
                    )
                )
                scores.append(score)
                methods.append(method)
                confidences.append(
                    confidence
                )

            posts_part[
                "Sentiment"
            ] = scores
            posts_part[
                "Sentiment_Label"
            ] = [
                sentiment_label(
                    score
                )
                for score
                in scores
            ]
            posts_part[
                "Sentiment Method"
            ] = methods
            posts_part[
                "Sentiment Confidence"
            ] = confidences

            frames.append(
                posts_part
            )

        if not coverage_part.empty:
            coverage_frames.append(
                coverage_part
            )

        errors.extend(
            errors_part
        )

if frames:
    posts = pd.concat(
        frames,
        ignore_index=True,
    )
    posts = (
        posts.drop_duplicates(
            subset=[
                "Platform",
                "Title",
                "Url",
            ],
            keep="first",
        )
        .reset_index(
            drop=True
        )
    )
else:
    posts = pd.DataFrame()

if coverage_frames:
    coverage = pd.concat(
        coverage_frames,
        ignore_index=True,
    ).drop_duplicates()
else:
    coverage = pd.DataFrame()

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
        for error in sorted(
            set(errors)
        ):
            st.write(error)

if posts.empty:
    st.warning(
        "No live public rows were returned."
    )
    st.stop()

comparison = platform_comparison(
    posts
)

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
        posts[
            "Platform"
        ].nunique()
    ),
)
k3.metric(
    "Total Engagement",
    int(
        posts[
            "Engagement"
        ]
        .fillna(0)
        .sum()
    ),
)
k4.metric(
    "Languages Observed",
    int(
        posts[
            "Language"
        ].nunique()
    ),
)

st.subheader(
    "Language Coverage"
)

language_counts = (
    posts[
        "Language"
    ]
    .value_counts()
    .rename_axis(
        "Language"
    )
    .reset_index(
        name="Rows"
    )
)

st.dataframe(
    language_counts,
    use_container_width=True,
    hide_index=True,
)

st.bar_chart(
    language_counts.set_index(
        "Language"
    )["Rows"]
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
    chart = go.Figure(
        go.Bar(
            x=comparison[
                "Platform"
            ],
            y=comparison[
                "Platform Risk"
            ],
            text=comparison[
                "Platform Risk"
            ],
            textposition="auto",
        )
    )

    chart.update_layout(
        yaxis_range=[
            0,
            100,
        ],
        height=430,
    )

    st.plotly_chart(
        chart,
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
        "No recurring terms appeared on multiple platforms."
    )
else:
    st.dataframe(
        overlap,
        use_container_width=True,
        hide_index=True,
    )

st.subheader(
    "High-Risk Social Narratives"
)

risk_posts = posts.copy()

risk_posts[
    "Risk Signal"
] = (
    (
        1
        - risk_posts[
            "Sentiment"
        ]
    )
    * 35
    + risk_posts[
        "Engagement"
    ]
    .fillna(0)
    .rank(
        pct=True,
        method="average",
    )
    * 30
).clip(
    0,
    100,
)

columns = [
    "Platform",
    "Title",
    "Author",
    "Published_At",
    "Language",
    "Search Language",
    "Search Query Used",
    "Engagement",
    "Sentiment",
    "Sentiment_Label",
    "Sentiment Method",
    "Sentiment Confidence",
    "Risk Signal",
    "Url",
]

st.dataframe(
    risk_posts.sort_values(
        "Risk Signal",
        ascending=False,
    )[
        [
            column
            for column
            in columns
            if column
            in risk_posts.columns
        ]
    ].head(50),
    use_container_width=True,
    hide_index=True,
)
