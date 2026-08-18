import os

import pandas as pd
import plotly.graph_objects as go
import streamlit as st

from utils.entity_selector import get_entity, get_entity_query
from utils.glossary import metric_help, render_glossary
from utils.multilingual_content import (
    CONTENT_LANGUAGES,
    NEWS_PROFILES,
    detect_script_language,
    get_selected_content_languages,
    resolve_query_alias,
    score_multilingual_sentiment,
    sentiment_label,
)
from utils.social_utils import (
    PLATFORM_CATALOG,
    calculate_social_metrics,
    collect_social_narratives,
    extract_terms,
    summarize_platforms,
)


st.set_page_config(
    page_title="Social Media Intelligence",
    page_icon="📣",
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
    platforms,
    youtube_api_key,
    limit,
):
    return collect_social_narratives(
        query=query,
        selected_platforms=list(platforms),
        youtube_api_key=youtube_api_key,
        limit_per_platform=limit,
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

st.title("📣 Social Media Intelligence")

render_glossary(
    [
        "SSI",
        "SVI",
        "NPI",
        "SRS",
        "RII",
        "NRRI",
        "OLI",
    ]
)

st.markdown(
    f"""
### Monitoring Multilingual Social Reputation Signals

**Selected Entity:** {display_name}

The platform searches available social sources using local-language
entity aliases where available, then preserves the original post language.
"""
)

c1, c2, c3, c4 = st.columns(4)
c1.metric("Type", entity["Entity_Type"])
c2.metric("Country", entity["Country"])
c3.metric("Sector", entity["Sector"])
c4.metric("Priority", entity["Priority"])

platform_options = list(
    PLATFORM_CATALOG.keys()
)

selected_platforms = st.sidebar.multiselect(
    "Platforms",
    platform_options,
    default=[
        "Hacker News",
        "Mastodon / Fediverse",
        "Reddit",
        "YouTube",
    ],
)

query = st.sidebar.text_input(
    "Social query",
    value=default_query,
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

search_plan = []

for code in content_languages:
    alias = resolve_query_alias(
        query,
        code,
    )

    search_plan.append(
        (
            code,
            alias,
        )
    )

# Deduplicate identical aliases while retaining the first language context.
seen_queries = set()
search_plan = [
    item
    for item in search_plan
    if not (
        item[1].lower()
        in seen_queries
        or seen_queries.add(
            item[1].lower()
        )
    )
]

if st.sidebar.button(
    "Refresh social data"
):
    load_social.clear()

frames = []
coverage_frames = []
errors = []

with st.spinner(
    "Collecting multilingual social narratives..."
):
    for code, current_query in search_plan:
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
            ] = language_name_by_code.get(
                code,
                code,
            )

            detected_codes = []

            for _, row in posts_part.iterrows():
                detected = detect_script_language(
                    row.get(
                        "Text",
                        "",
                    ),
                    code,
                )

                detected_codes.append(
                    detected
                )

            posts_part[
                "Language Code"
            ] = detected_codes

            posts_part[
                "Language"
            ] = [
                NEWS_PROFILES.get(
                    detected,
                    {},
                ).get(
                    "label",
                    detected,
                )
                for detected
                in detected_codes
            ]

            sentiment_values = []
            sentiment_methods = []
            sentiment_confidences = []

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

                sentiment_values.append(
                    score
                )
                sentiment_methods.append(
                    method
                )
                sentiment_confidences.append(
                    confidence
                )

            posts_part[
                "Sentiment"
            ] = sentiment_values

            posts_part[
                "Sentiment_Label"
            ] = [
                sentiment_label(
                    score
                )
                for score
                in sentiment_values
            ]

            posts_part[
                "Sentiment Method"
            ] = sentiment_methods

            posts_part[
                "Sentiment Confidence"
            ] = sentiment_confidences

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

if errors:
    with st.expander(
        "Source connection notes"
    ):
        for error in sorted(
            set(errors)
        ):
            st.write(error)

st.subheader(
    "Source Coverage"
)

st.dataframe(
    coverage,
    use_container_width=True,
    hide_index=True,
)

if posts.empty:
    st.warning(
        "No live social rows returned."
    )
    st.stop()

metrics = calculate_social_metrics(
    posts
)

platform_summary = summarize_platforms(
    posts
)

st.subheader(
    "Executive Overview"
)

k1, k2, k3, k4, k5 = st.columns(5)
k1.metric(
    "SSI",
    metrics["SSI"],
    help=metric_help("SSI"),
)
k2.metric(
    "SVI",
    metrics["SVI"],
    help=metric_help("SVI"),
)
k3.metric(
    "NPI",
    metrics["NPI"],
    help=metric_help("NPI"),
)
k4.metric(
    "SRS",
    metrics["SRS"],
    help=metric_help("SRS"),
)
k5.metric(
    "Languages Observed",
    int(
        posts[
            "Language"
        ].nunique()
    ),
)

st.subheader(
    "Language Signals"
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
    "Platform Comparison"
)

st.dataframe(
    platform_summary,
    use_container_width=True,
    hide_index=True,
)

left, right = st.columns(2)

with left:
    volume_chart = go.Figure()
    volume_chart.add_trace(
        go.Bar(
            x=platform_summary[
                "Platform"
            ],
            y=platform_summary[
                "Mentions"
            ],
            name="Mentions",
        )
    )
    volume_chart.add_trace(
        go.Bar(
            x=platform_summary[
                "Platform"
            ],
            y=platform_summary[
                "Engagement"
            ],
            name="Engagement",
        )
    )
    volume_chart.update_layout(
        barmode="group",
        height=420,
    )
    st.plotly_chart(
        volume_chart,
        use_container_width=True,
    )

with right:
    sentiment_chart = go.Figure(
        go.Bar(
            x=platform_summary[
                "Platform"
            ],
            y=platform_summary[
                "Average Sentiment"
            ],
        )
    )
    sentiment_chart.update_layout(
        height=420,
        yaxis_range=[
            -1,
            1,
        ],
    )
    st.plotly_chart(
        sentiment_chart,
        use_container_width=True,
    )

st.subheader(
    "Trending Social Narratives"
)

terms = extract_terms(
    posts
)

if terms.empty:
    st.info(
        "No recurring narrative terms detected."
    )
else:
    st.dataframe(
        terms,
        use_container_width=True,
        hide_index=True,
    )

st.subheader(
    "Narrative Records"
)

record_columns = [
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
    "Geo_Scope",
    "Data_Status",
    "Url",
]

st.dataframe(
    posts[
        [
            column
            for column
            in record_columns
            if column
            in posts.columns
        ]
    ],
    use_container_width=True,
    hide_index=True,
)

st.info(
    "For non-English social content, sentiment uses transparent "
    "prototype language lexicons. Platform access remains subject "
    "to official API permissions and public-data rules."
)
