import pandas as pd
import plotly.graph_objects as go
import streamlit as st

from utils.multilingual_content import (
    fetch_multilingual_news,
    get_selected_content_languages,
    language_coverage,
)


st.set_page_config(
    page_title="Narrative Intelligence",
    page_icon="🧠",
    layout="wide",
)

st.title("🧠 Narrative Intelligence")

try:
    registry_df = pd.read_csv(
        "config/entity_registry.csv",
        encoding="utf-8-sig",
    )
except FileNotFoundError:
    st.error(
        "Registry file not found: config/entity_registry.csv"
    )
    st.stop()

sector_filter = st.sidebar.multiselect(
    "Filter by Sector",
    sorted(
        registry_df["Sector"]
        .dropna()
        .unique()
        .tolist()
    ),
)

priority_filter = st.sidebar.multiselect(
    "Filter by Priority",
    sorted(
        registry_df["Priority"]
        .dropna()
        .unique()
        .tolist()
    ),
)

filtered_registry = registry_df.copy()

if sector_filter:
    filtered_registry = filtered_registry[
        filtered_registry["Sector"].isin(
            sector_filter
        )
    ]

if priority_filter:
    filtered_registry = filtered_registry[
        filtered_registry["Priority"].isin(
            priority_filter
        )
    ]

selected_entities = st.sidebar.multiselect(
    "Select Organizations",
    filtered_registry[
        "Entity_Name"
    ].tolist(),
    default=(
        filtered_registry[
            "Entity_Name"
        ]
        .head(5)
        .tolist()
    ),
)

if not selected_entities:
    st.warning(
        "Select at least one organization."
    )
    st.stop()

selected_df = filtered_registry[
    filtered_registry[
        "Entity_Name"
    ].isin(
        selected_entities
    )
]

content_languages = (
    get_selected_content_languages()
)


@st.cache_data(ttl=1800, show_spinner=False)
def load_narratives(
    query,
    languages,
):
    return fetch_multilingual_news(
        query,
        languages=list(languages),
        limit_per_language=7,
    )


rows = []

with st.spinner(
    "Collecting multilingual narratives..."
):
    for _, entity in selected_df.iterrows():
        news_df = load_narratives(
            entity["News_Query"],
            tuple(content_languages),
        )

        if news_df.empty:
            continue

        news_df = news_df.copy()
        news_df["Entity"] = entity[
            "Entity_Name"
        ]
        news_df["Short Name"] = entity[
            "Short_Name"
        ]

        news_df[
            "Narrative Risk"
        ] = news_df[
            "Sentiment"
        ].apply(
            lambda score:
            "High Risk Narrative"
            if score <= -0.5
            else (
                "Moderate Risk Narrative"
                if score <= -0.2
                else "Low Risk Narrative"
            )
        )

        rows.append(news_df)

if not rows:
    st.error(
        "No multilingual narrative data available."
    )
    st.stop()

narrative_df = pd.concat(
    rows,
    ignore_index=True,
)

st.subheader(
    "Narrative Feed"
)

st.dataframe(
    narrative_df[
        [
            "Entity",
            "Short Name",
            "Headline",
            "Language",
            "Edition Country",
            "Source",
            "Sentiment",
            "Sentiment Label",
            "Narrative Risk",
            "Sentiment Method",
            "Sentiment Confidence",
            "Published",
            "Link",
        ]
    ],
    use_container_width=True,
    hide_index=True,
)

st.subheader(
    "Multilingual Narrative Coverage"
)

coverage = language_coverage(
    narrative_df
)

st.dataframe(
    coverage,
    use_container_width=True,
    hide_index=True,
)

st.bar_chart(
    coverage.set_index(
        "Language"
    )["Narratives"]
)

st.subheader(
    "High-Risk Narratives"
)

high_risk_df = narrative_df[
    narrative_df[
        "Narrative Risk"
    ] != "Low Risk Narrative"
]

if high_risk_df.empty:
    st.info(
        "No high-risk narratives detected."
    )
else:
    st.dataframe(
        high_risk_df.sort_values(
            "Sentiment"
        )[
            [
                "Short Name",
                "Headline",
                "Language",
                "Edition Country",
                "Source",
                "Sentiment",
                "Narrative Risk",
                "Sentiment Confidence",
                "Link",
            ]
        ],
        use_container_width=True,
        hide_index=True,
    )

left, right = st.columns(2)

with left:
    st.subheader(
        "Narrative Sentiment Distribution"
    )

    sentiment_counts = (
        narrative_df[
            "Sentiment Label"
        ]
        .value_counts()
        .rename_axis("Sentiment")
        .reset_index(
            name="Narratives"
        )
    )

    sentiment_fig = go.Figure(
        go.Pie(
            labels=sentiment_counts[
                "Sentiment"
            ],
            values=sentiment_counts[
                "Narratives"
            ],
            hole=0.45,
        )
    )

    st.plotly_chart(
        sentiment_fig,
        use_container_width=True,
    )

with right:
    st.subheader(
        "Narrative Risk Distribution"
    )

    risk_counts = (
        narrative_df[
            "Narrative Risk"
        ]
        .value_counts()
        .rename_axis(
            "Risk"
        )
        .reset_index(
            name="Narratives"
        )
    )

    risk_fig = go.Figure(
        go.Bar(
            x=risk_counts["Risk"],
            y=risk_counts[
                "Narratives"
            ],
            text=risk_counts[
                "Narratives"
            ],
            textposition="auto",
        )
    )

    st.plotly_chart(
        risk_fig,
        use_container_width=True,
    )

st.subheader(
    "Most Negative Narratives by Organization"
)

for short_name in narrative_df[
    "Short Name"
].unique():
    company_df = narrative_df[
        narrative_df[
            "Short Name"
        ] == short_name
    ]

    st.write(
        f"### {short_name}"
    )

    st.dataframe(
        company_df.sort_values(
            "Sentiment"
        )[
            [
                "Headline",
                "Language",
                "Edition Country",
                "Source",
                "Sentiment",
                "Sentiment Confidence",
                "Link",
            ]
        ].head(8),
        use_container_width=True,
        hide_index=True,
    )

st.info(
    "Original-language headlines are preserved. "
    "This avoids hiding cultural and regional narrative differences "
    "behind automatic translation."
)
