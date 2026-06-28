import streamlit as st
import pandas as pd
import numpy as np
import yfinance as yf
import feedparser

from vaderSentiment.vaderSentiment import SentimentIntensityAnalyzer
from urllib.parse import quote_plus
from utils.glossary import metric_help, render_glossary

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
    st.error("Registry file not found: config/entity_registry.csv")
    st.stop()

required_columns = [
    "Entity_Name",
    "Short_Name",
    "Entity_Type",
    "Ticker",
    "Country",
    "Sector",
    "Priority",
    "News_Query",
]

missing_columns = [
    column
    for column in required_columns
    if column not in registry_df.columns
]

if missing_columns:
    st.error(
        "Registry file is missing required columns: "
        + ", ".join(missing_columns)
    )
    st.stop()

language = st.sidebar.selectbox(
    "Language",
    ["EN", "RU"],
)

if language == "RU":
    period_title = "Analysis Period"
    page_title = "Executive Overview"
else:
    period_title = "Analysis Period"
    page_title = "Executive Overview"

st.header(page_title)

time_range = st.sidebar.selectbox(
    period_title,
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
        filtered_registry["Sector"].isin(sector_filter)
    ]

if priority_filter:
    filtered_registry = filtered_registry[
        filtered_registry["Priority"].isin(priority_filter)
    ]

selected_entities = st.sidebar.multiselect(
    "Select Organizations",
    filtered_registry["Entity_Name"].tolist(),
    default=filtered_registry["Entity_Name"].head(5).tolist(),
)

if not selected_entities:
    st.warning("Select at least one organization.")
    st.stop()

selected_df = filtered_registry[
    filtered_registry["Entity_Name"].isin(selected_entities)
]

analyzer = SentimentIntensityAnalyzer()


def has_value(value):
    text = str(value).strip()
    return bool(text) and text.lower() != "nan"


@st.cache_data(ttl=1800)
def get_news_scores(query):
    encoded_query = quote_plus(query)

    feed = feedparser.parse(
        f"https://news.google.com/rss/search?q={encoded_query}&hl=en-US&gl=US&ceid=US:en"
    )

    rows = []

    for entry in feed.entries[:15]:
        title = entry.title
        score = analyzer.polarity_scores(title)["compound"]

        rows.append({
            "Headline": title,
            "Sentiment": float(score),
        })

    return pd.DataFrame(rows)


@st.cache_data(ttl=3600)
def get_market_volatility(ticker, start_date):
    if not has_value(ticker):
        return 0

    stock = yf.download(
        ticker,
        start=start_date,
        progress=False,
        auto_adjust=True,
    )

    if stock.empty:
        return 0

    stock["Returns"] = stock["Close"].pct_change()
    volatility = stock["Returns"].rolling(21).std().dropna()

    if volatility.empty:
        return 0

    return float(volatility.iloc[-1])


results = []
keyword_results = []

for _, entity in selected_df.iterrows():
    entity_name = entity["Entity_Name"]
    short_name = entity["Short_Name"]
    ticker = entity["Ticker"]
    news_query = entity["News_Query"]

    news_df = get_news_scores(news_query)

    if news_df.empty:
        continue

    market_volatility = get_market_volatility(
        ticker,
        start_date,
    )

    scores = news_df["Sentiment"].tolist()

    for _, news_row in news_df.iterrows():
        if news_row["Sentiment"] <= -0.2:
            keyword_results.append({
                "Entity": short_name,
                "Headline": news_row["Headline"],
                "Sentiment": round(float(news_row["Sentiment"]), 3),
                "Risk Level": "Negative Narrative",
            })

    dss = np.mean(np.abs(scores))
    sentiment_volatility = np.std(scores)

    reputation_risk = (
        sentiment_volatility * 45
        + dss * 35
        + market_volatility * 20
    )

    reputation_risk = min(100, reputation_risk)

    if reputation_risk >= 70:
        risk_level = "High"
    elif reputation_risk >= 40:
        risk_level = "Medium"
    else:
        risk_level = "Low"

    results.append({
        "Entity": entity_name,
        "Short Name": short_name,
        "Ticker": ticker,
        "Country": entity["Country"],
        "Sector": entity["Sector"],
        "DSS": round(float(dss), 3),
        "Sentiment Volatility": round(float(sentiment_volatility), 3),
        "Market Volatility": round(float(market_volatility), 4),
        "Reputation Risk": round(float(reputation_risk), 2),
        "Risk Level": risk_level,
    })

risk_df = pd.DataFrame(results)
keyword_df = pd.DataFrame(keyword_results)

if risk_df.empty:
    st.error("No data available. Try different organizations or check News_Query values.")
    st.stop()

avg_dss = round(risk_df["DSS"].mean(), 3)
avg_rr = round(risk_df["Reputation Risk"].mean(), 2)
avg_sv = round(risk_df["Sentiment Volatility"].mean(), 3)

col1, col2, col3, col4 = st.columns(4)

col1.metric("Average DSS", avg_dss, help=metric_help("DSS"))
col2.metric("Average Reputation Risk", avg_rr, help="Composite reputation pressure from sentiment volatility, digital sentiment strength, and market volatility where available.")
col3.metric("Average Sentiment Volatility", avg_sv, help="Standard deviation of sentiment scores across monitored headlines.")
col4.metric("Organizations Monitored", len(risk_df), help="Number of selected organisations with available news data.")

st.subheader("Organization Risk Ranking")

ranking_df = risk_df.sort_values(
    by="Reputation Risk",
    ascending=False,
)

ranking_df["Rank"] = range(1, len(ranking_df) + 1)

st.dataframe(
    ranking_df,
    use_container_width=True,
    hide_index=True,
)

st.subheader("Risk Alert Engine")

for _, row in ranking_df.iterrows():
    entity_name = row["Short Name"]
    reputation_risk = row["Reputation Risk"]

    if reputation_risk >= 70:
        st.error(f"{entity_name}: HIGH REPUTATION RISK DETECTED")
    elif reputation_risk >= 40:
        st.warning(f"{entity_name}: MODERATE REPUTATION RISK")
    else:
        st.success(f"{entity_name}: LOW REPUTATION RISK")

st.subheader("Top Negative Narratives")

if keyword_df.empty:
    st.info("No high-risk negative narratives detected.")
else:
    negative_df = keyword_df.sort_values(
        by="Sentiment",
    ).head(10)

    st.dataframe(
        negative_df,
        use_container_width=True,
        hide_index=True,
    )

st.subheader("Executive Intelligence Insights")

for _, row in ranking_df.iterrows():
    entity_name = row["Short Name"]
    reputation_risk = row["Reputation Risk"]

    if reputation_risk >= 70:
        insight = (
            f"{entity_name} demonstrates severe reputational instability "
            f"driven by elevated sentiment volatility and negative narrative exposure."
        )
    elif reputation_risk >= 40:
        insight = (
            f"{entity_name} demonstrates moderate reputational pressure "
            f"with increasing narrative volatility."
        )
    else:
        insight = (
            f"{entity_name} currently maintains relatively stable reputation conditions "
            f"with limited negative narrative escalation."
        )

    st.info(insight)
