import numpy as np
import pandas as pd
import plotly.graph_objects as go
import streamlit as st

from utils.glossary import render_glossary
from utils.multilingual_content import (
    fetch_multilingual_news,
    get_selected_content_languages,
    language_coverage,
)


st.set_page_config(
    page_title="Sentiment & Subjectivity",
    page_icon="💬",
    layout="wide",
)

st.title(
    "💬 Sentiment & Subjectivity Intelligence"
)

render_glossary(["VADER"])

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
def load_sentiment(
    query,
    languages,
):
    return fetch_multilingual_news(
        query,
        languages=list(languages),
        limit_per_language=7,
    )


frames = []

with st.spinner(
    "Collecting multilingual sentiment evidence..."
):
    for _, entity in selected_df.iterrows():
        news_df = load_sentiment(
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

        frames.append(
            news_df
        )

if not frames:
    st.error(
        "No multilingual sentiment data available."
    )
    st.stop()

df = pd.concat(
    frames,
    ignore_index=True,
)

st.subheader(
    "Sentiment and Subjectivity Dataset"
)

st.dataframe(
    df[
        [
            "Entity",
            "Short Name",
            "Headline",
            "Language",
            "Edition Country",
            "Source",
            "Sentiment",
            "Sentiment Label",
            "Sentiment Method",
            "Sentiment Confidence",
            "Subjectivity",
            "Subjectivity Method",
            "Link",
        ]
    ],
    use_container_width=True,
    hide_index=True,
)

st.subheader(
    "Language Coverage"
)

coverage = language_coverage(
    df
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
    "Organization-Level Sentiment Summary"
)

summary_df = (
    df.groupby(
        "Short Name"
    )
    .agg(
        Average_Sentiment=(
            "Sentiment",
            "mean",
        ),
        Sentiment_Volatility=(
            "Sentiment",
            "std",
        ),
        Languages=(
            "Language",
            "nunique",
        ),
        Narratives=(
            "Headline",
            "count",
        ),
        English_Subjectivity=(
            "Subjectivity",
            "mean",
        ),
    )
    .reset_index()
)

summary_df[
    "Average Sentiment"
] = summary_df[
    "Average_Sentiment"
].round(3)

summary_df[
    "Sentiment Volatility"
] = summary_df[
    "Sentiment_Volatility"
].fillna(0).round(3)

summary_df[
    "English Subjectivity"
] = summary_df[
    "English_Subjectivity"
].round(3)

summary_df = summary_df.drop(
    columns=[
        "Average_Sentiment",
        "Sentiment_Volatility",
        "English_Subjectivity",
    ]
)

st.dataframe(
    summary_df,
    use_container_width=True,
    hide_index=True,
)

st.subheader(
    "Sentiment by Language"
)

language_sentiment = (
    df.groupby(
        "Language"
    )["Sentiment"]
    .mean()
    .sort_values()
)

st.bar_chart(
    language_sentiment
)

st.subheader(
    "Sentiment vs Subjectivity"
)

english_subjective = df[
    df["Subjectivity"].notna()
].copy()

if english_subjective.empty:
    st.info(
        "Validated subjectivity scoring is currently available "
        "only for English content. Other-language subjectivity "
        "is intentionally left unscored rather than estimated unreliably."
    )
else:
    scatter = go.Figure(
        go.Scatter(
            x=english_subjective[
                "Sentiment"
            ],
            y=english_subjective[
                "Subjectivity"
            ],
            mode="markers",
            text=english_subjective[
                "Headline"
            ],
            marker={
                "size": 9,
            },
        )
    )

    scatter.update_layout(
        xaxis_title="Sentiment",
        yaxis_title="Subjectivity",
        height=550,
    )

    st.plotly_chart(
        scatter,
        use_container_width=True,
    )

st.subheader(
    "Low-Confidence Sentiment Records"
)

low_confidence = df[
    df[
        "Sentiment Confidence"
    ].eq("Low")
]

if low_confidence.empty:
    st.success(
        "No low-confidence sentiment records in this run."
    )
else:
    st.dataframe(
        low_confidence[
            [
                "Headline",
                "Language",
                "Sentiment",
                "Sentiment Method",
                "Source",
                "Link",
            ]
        ].head(30),
        use_container_width=True,
        hide_index=True,
    )

st.info(
    "English uses VADER. Other languages currently use transparent "
    "prototype lexicons and expose their confidence. This is safer "
    "than applying an English sentiment model to every language."
)
