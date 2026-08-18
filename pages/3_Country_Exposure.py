import pandas as pd
import plotly.graph_objects as go
import streamlit as st

from utils.multilingual_content import (
    fetch_multilingual_news,
    get_selected_content_languages,
    language_coverage,
    safe_sentiment_stats,
)


st.set_page_config(
    page_title="Country Exposure",
    page_icon="🌍",
    layout="wide",
)

st.title("🌍 Country Exposure Intelligence")

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

selected_countries = st.sidebar.multiselect(
    "Filter by Country",
    sorted(
        registry_df["Country"]
        .dropna()
        .unique()
        .tolist()
    ),
)

selected_sectors = st.sidebar.multiselect(
    "Filter by Sector",
    sorted(
        registry_df["Sector"]
        .dropna()
        .unique()
        .tolist()
    ),
)

filtered_registry = registry_df.copy()

if selected_countries:
    filtered_registry = filtered_registry[
        filtered_registry["Country"].isin(
            selected_countries
        )
    ]

if selected_sectors:
    filtered_registry = filtered_registry[
        filtered_registry["Sector"].isin(
            selected_sectors
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
        .head(8)
        .tolist()
    ),
)

if not selected_entities:
    st.warning(
        "Select at least one organization."
    )
    st.stop()

filtered_registry = filtered_registry[
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
def load_news(
    query,
    languages,
):
    return fetch_multilingual_news(
        query,
        languages=list(languages),
        limit_per_language=5,
    )


rows = []
all_news = []

with st.spinner(
    "Collecting multilingual country exposure..."
):
    for _, entity in filtered_registry.iterrows():
        news_df = load_news(
            entity["News_Query"],
            tuple(content_languages),
        )

        if news_df.empty:
            continue

        news_df = news_df.copy()
        news_df["Entity"] = entity[
            "Short_Name"
        ]

        all_news.append(news_df)

        stats = safe_sentiment_stats(
            news_df
        )

        reputation_risk = min(
            100.0,
            (
                stats["std"] * 60
                + stats["abs_mean"] * 40
            ),
        )

        rows.append(
            {
                "Entity":
                entity["Entity_Name"],
                "Short Name":
                entity["Short_Name"],
                "Country":
                entity["Country"],
                "Sector":
                entity["Sector"],
                "Priority":
                entity["Priority"],
                "Narrative Volume":
                stats["count"],
                "Languages Observed":
                int(
                    news_df[
                        "Language"
                    ].nunique()
                ),
                "Negative Narratives":
                int(
                    news_df[
                        "Sentiment"
                    ].le(-0.3).sum()
                ),
                "Average Sentiment":
                round(
                    stats["mean"],
                    3,
                ),
                "Sentiment Volatility":
                round(
                    stats["std"],
                    3,
                ),
                "Reputation Risk":
                round(
                    reputation_risk,
                    2,
                ),
            }
        )

df = pd.DataFrame(rows)

if df.empty:
    st.error(
        "No country exposure data available."
    )
    st.stop()

country_df = (
    df.groupby("Country")
    .agg(
        {
            "Entity": "count",
            "Narrative Volume": "sum",
            "Languages Observed": "max",
            "Negative Narratives": "sum",
            "Average Sentiment": "mean",
            "Sentiment Volatility": "mean",
            "Reputation Risk": "mean",
        }
    )
    .reset_index()
    .rename(
        columns={
            "Entity":
            "Organizations Monitored",
            "Reputation Risk":
            "Average Reputation Risk",
        }
    )
)

country_df[
    "Average Reputation Risk"
] = country_df[
    "Average Reputation Risk"
].round(2)

st.subheader(
    "Country Exposure Summary"
)

st.dataframe(
    country_df,
    use_container_width=True,
    hide_index=True,
)

st.subheader(
    "Country Risk Ranking"
)

ranking = country_df.sort_values(
    "Average Reputation Risk",
    ascending=False,
)

fig = go.Figure(
    go.Bar(
        x=ranking["Country"],
        y=ranking[
            "Average Reputation Risk"
        ],
        text=ranking[
            "Average Reputation Risk"
        ],
        textposition="auto",
    )
)

fig.update_layout(
    height=500,
    title=(
        "Average Reputation Risk by Country"
    ),
)

st.plotly_chart(
    fig,
    use_container_width=True,
)

if all_news:
    combined = pd.concat(
        all_news,
        ignore_index=True,
    )

    st.subheader(
        "Global Language Coverage"
    )

    coverage = language_coverage(
        combined
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
    "Organization Exposure by Country"
)

st.dataframe(
    df.sort_values(
        [
            "Country",
            "Reputation Risk",
        ],
        ascending=[
            True,
            False,
        ],
    ),
    use_container_width=True,
    hide_index=True,
)
