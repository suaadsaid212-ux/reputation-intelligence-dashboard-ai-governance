import numpy as np
import pandas as pd
import streamlit as st
import yfinance as yf

from utils.glossary import metric_help, render_glossary
from utils.multilingual_content import (
    fetch_multilingual_news,
    get_selected_content_languages,
    language_coverage,
    safe_sentiment_stats,
)


st.set_page_config(
    page_title="Executive Overview",
    page_icon="📊",
    layout="wide",
)

st.title("📊 Executive Overview")
render_glossary(["DSS", "RII", "OLI", "SRI", "VADER"])

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

time_range = st.sidebar.selectbox(
    "Analysis Period",
    [
        "1 Month",
        "3 Months",
        "6 Months",
        "1 Year",
        "3 Years",
        "5 Years",
    ],
)

start_dates = {
    "1 Month": "2026-05-01",
    "3 Months": "2026-03-01",
    "6 Months": "2025-12-01",
    "1 Year": "2025-06-01",
    "3 Years": "2023-06-01",
    "5 Years": "2021-06-01",
}

start_date = start_dates[time_range]

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
    filtered_registry["Entity_Name"].tolist(),
    default=(
        filtered_registry["Entity_Name"]
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
    filtered_registry["Entity_Name"].isin(
        selected_entities
    )
]

content_languages = (
    get_selected_content_languages()
)

st.caption(
    "Content collection languages: "
    + ", ".join(content_languages)
)


def has_value(value):
    text = str(value).strip()
    return (
        bool(text)
        and text.lower() != "nan"
    )


@st.cache_data(ttl=1800, show_spinner=False)
def get_news_scores(
    query,
    languages,
):
    return fetch_multilingual_news(
        query=query,
        languages=list(languages),
        limit_per_language=6,
    )


@st.cache_data(ttl=3600, show_spinner=False)
def get_market_volatility(
    ticker,
    start_date,
):
    if not has_value(ticker):
        return 0.0

    try:
        stock = yf.download(
            ticker,
            start=start_date,
            progress=False,
            auto_adjust=True,
        )
    except Exception:
        return 0.0

    if stock.empty:
        return 0.0

    stock["Returns"] = (
        stock["Close"].pct_change()
    )

    volatility = (
        stock["Returns"]
        .rolling(21)
        .std()
        .dropna()
    )

    if volatility.empty:
        return 0.0

    value = volatility.iloc[-1]

    try:
        return float(value)
    except Exception:
        return float(
            value.squeeze()
        )


results = []
negative_rows = []
all_news = []

with st.spinner(
    "Collecting multilingual evidence..."
):
    for _, entity in selected_df.iterrows():
        query = entity["News_Query"]

        news_df = get_news_scores(
            query,
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

        market_volatility = (
            get_market_volatility(
                entity["Ticker"],
                start_date,
            )
        )

        dss = stats["abs_mean"]
        sentiment_volatility = (
            stats["std"]
        )

        reputation_risk = min(
            100.0,
            sentiment_volatility * 45
            + dss * 35
            + market_volatility * 20,
        )

        if reputation_risk >= 70:
            risk_level = "High"
        elif reputation_risk >= 40:
            risk_level = "Medium"
        else:
            risk_level = "Low"

        results.append(
            {
                "Entity":
                entity["Entity_Name"],
                "Short Name":
                entity["Short_Name"],
                "Ticker":
                entity["Ticker"],
                "Country":
                entity["Country"],
                "Sector":
                entity["Sector"],
                "Narratives":
                stats["count"],
                "Languages":
                int(
                    news_df[
                        "Language"
                    ].nunique()
                ),
                "DSS":
                round(dss, 3),
                "Sentiment Volatility":
                round(
                    sentiment_volatility,
                    3,
                ),
                "Market Volatility":
                round(
                    market_volatility,
                    4,
                ),
                "Reputation Risk":
                round(
                    reputation_risk,
                    2,
                ),
                "Risk Level":
                risk_level,
            }
        )

        entity_negative = (
            news_df[
                news_df["Sentiment"]
                <= -0.3
            ]
            .copy()
        )

        if not entity_negative.empty:
            entity_negative[
                "Entity"
            ] = entity["Short_Name"]

            negative_rows.append(
                entity_negative
            )

risk_df = pd.DataFrame(results)

if risk_df.empty:
    st.error(
        "No multilingual news data available. "
        "Try fewer languages or different organizations."
    )
    st.stop()

avg_dss = round(
    risk_df["DSS"].mean(),
    3,
)
avg_rr = round(
    risk_df[
        "Reputation Risk"
    ].mean(),
    2,
)
avg_sv = round(
    risk_df[
        "Sentiment Volatility"
    ].mean(),
    3,
)

col1, col2, col3, col4 = st.columns(4)

col1.metric(
    "Average DSS",
    avg_dss,
    help=metric_help("DSS"),
)
col2.metric(
    "Average Reputation Risk",
    avg_rr,
)
col3.metric(
    "Average Sentiment Volatility",
    avg_sv,
)
col4.metric(
    "Organizations Monitored",
    len(risk_df),
)

st.subheader(
    "Organization Risk Ranking"
)

ranking_df = risk_df.sort_values(
    by="Reputation Risk",
    ascending=False,
).copy()

ranking_df["Rank"] = range(
    1,
    len(ranking_df) + 1,
)

st.dataframe(
    ranking_df,
    use_container_width=True,
    hide_index=True,
)

st.subheader(
    "Multilingual Evidence Coverage"
)

if all_news:
    combined_news = pd.concat(
        all_news,
        ignore_index=True,
    )

    coverage_df = language_coverage(
        combined_news
    )

    st.dataframe(
        coverage_df,
        use_container_width=True,
        hide_index=True,
    )

    st.bar_chart(
        coverage_df.set_index(
            "Language"
        )["Narratives"]
    )

st.subheader("Risk Alert Engine")

for _, row in ranking_df.iterrows():
    name = row["Short Name"]
    risk = row["Reputation Risk"]

    if risk >= 70:
        st.error(
            f"{name}: HIGH REPUTATION RISK DETECTED"
        )
    elif risk >= 40:
        st.warning(
            f"{name}: MODERATE REPUTATION RISK"
        )
    else:
        st.success(
            f"{name}: LOW REPUTATION RISK"
        )

st.subheader(
    "Top Negative Narratives"
)

if negative_rows:
    negative_df = pd.concat(
        negative_rows,
        ignore_index=True,
    )

    display = negative_df.sort_values(
        "Sentiment"
    ).head(20)

    st.dataframe(
        display[
            [
                "Entity",
                "Headline",
                "Language",
                "Edition Country",
                "Source",
                "Sentiment",
                "Sentiment Method",
                "Sentiment Confidence",
                "Link",
            ]
        ],
        use_container_width=True,
        hide_index=True,
    )
else:
    st.info(
        "No high-risk negative narratives detected."
    )

st.info(
    "Multilingual sentiment outside English uses lightweight "
    "language-specific prototype lexicons. The original headline "
    "is preserved and each score shows its method and confidence."
)
