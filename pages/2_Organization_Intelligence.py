import streamlit as st
import pandas as pd
import numpy as np
import yfinance as yf
import plotly.graph_objects as go
import feedparser
import matplotlib.pyplot as plt

from wordcloud import WordCloud
from vaderSentiment.vaderSentiment import SentimentIntensityAnalyzer
from urllib.parse import quote_plus

from utils.entity_selector import get_entity, get_entity_query
from utils.glossary import metric_help, render_glossary

st.set_page_config(
    page_title="Organization Intelligence",
    page_icon="🏢",
    layout="wide",
)

entity = get_entity()

entity_name = entity["Entity_Name"]
display_name = entity["Short_Name"]
ticker = str(entity.get("Ticker", "")).strip()
news_query = get_entity_query(entity, "News_Query")

st.title("🏢 Organization Intelligence")

render_glossary(["DSS", "VADER"])

st.markdown(f"""
### Single-Entity Intelligence Profile

**Selected Entity:** {display_name}

This page combines organization profile data, market data when available,
news sentiment, narrative signals, and DSS components.
""")

c1, c2, c3, c4 = st.columns(4)

c1.metric("Type", entity["Entity_Type"])
c2.metric("Country", entity["Country"])
c3.metric("Sector", entity["Sector"])
c4.metric("Priority", entity["Priority"])

st.caption(f"News query: {news_query}")

st.divider()

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


def has_value(value):
    text = str(value).strip()
    return bool(text) and text.lower() != "nan"


@st.cache_data(ttl=3600)
def get_stock_data(ticker, start_date):
    if not has_value(ticker):
        return pd.DataFrame()

    return yf.download(
        ticker,
        start=start_date,
        progress=False,
        auto_adjust=True,
    )


@st.cache_data(ttl=1800)
def get_news_data(query):
    encoded_query = quote_plus(query)

    feed = feedparser.parse(
        f"https://news.google.com/rss/search?q={encoded_query}&hl=en-US&gl=US&ceid=US:en"
    )

    return [
        entry.title
        for entry in feed.entries[:20]
    ]


analyzer = SentimentIntensityAnalyzer()

stock = get_stock_data(
    ticker,
    start_date,
)

if stock.empty:
    st.info(
        "No financial market data available for this entity. "
        "This is normal for governments, universities, and international organizations."
    )
else:
    stock["Returns"] = stock["Close"].pct_change()
    stock["Volatility"] = stock["Returns"].rolling(21).std()

    st.subheader(f"{display_name} Stock Performance")

    close_prices = stock["Close"].squeeze()

    stock_fig = go.Figure()

    stock_fig.add_trace(
        go.Scatter(
            x=close_prices.index,
            y=close_prices.values,
            mode="lines",
            name=display_name,
        )
    )

    stock_fig.update_layout(
        height=550,
        xaxis_title="Date",
        yaxis_title="Adjusted Close",
    )

    st.plotly_chart(
        stock_fig,
        use_container_width=True,
    )

    st.subheader(f"{display_name} Volatility Timeline")

    volatility_series = stock["Volatility"].fillna(0).squeeze()

    vol_fig = go.Figure()

    vol_fig.add_trace(
        go.Scatter(
            x=volatility_series.index,
            y=volatility_series.values,
            mode="lines",
            name="Volatility",
        )
    )

    vol_fig.update_layout(
        height=500,
        xaxis_title="Date",
        yaxis_title="Rolling Volatility",
    )

    st.plotly_chart(
        vol_fig,
        use_container_width=True,
    )

st.subheader(f"{display_name} News and Sentiment")

headlines = get_news_data(news_query)

news_rows = []
scores = []

for title in headlines:
    score = analyzer.polarity_scores(title)["compound"]

    if score >= 0.3:
        label = "Positive"
    elif score <= -0.3:
        label = "Negative"
    else:
        label = "Neutral"

    news_rows.append({
        "Headline": title,
        "Sentiment": round(float(score), 3),
        "Label": label,
    })

    scores.append(score)

news_df = pd.DataFrame(news_rows)

if news_df.empty:
    st.warning("No news data found for this entity.")
    st.stop()

st.dataframe(
    news_df,
    use_container_width=True,
    hide_index=True,
)

if scores:
    dss = np.mean(np.abs(scores))
    sentiment_volatility = np.std(scores)
    reputation_risk = (
        0.6 * sentiment_volatility
        + 0.4 * dss
    ) * 100

    col1, col2, col3 = st.columns(3)

    col1.metric("DSS", round(float(dss), 3), help=metric_help("DSS"))
    col2.metric("Sentiment Volatility", round(float(sentiment_volatility), 3), help="Variation in sentiment scores across monitored headlines.")
    col3.metric("Reputation Risk", round(float(reputation_risk), 2), help="Prototype risk score combining sentiment volatility and digital sentiment strength.")

st.subheader(f"{display_name} Sentiment Distribution")

distribution = news_df["Label"].value_counts()

pie_fig = go.Figure(
    data=[
        go.Pie(
            labels=distribution.index,
            values=distribution.values,
            hole=0.45,
        )
    ]
)

pie_fig.update_layout(
    height=500,
)

st.plotly_chart(
    pie_fig,
    use_container_width=True,
)

st.subheader(f"{display_name} Narrative Word Cloud")

text = " ".join(headlines)

wordcloud = WordCloud(
    width=1200,
    height=600,
    background_color="white",
    colormap="Reds",
).generate(text)

fig, ax = plt.subplots(figsize=(14, 7))

ax.imshow(
    wordcloud,
    interpolation="bilinear",
)

ax.axis("off")

st.pyplot(fig)

st.subheader(f"{display_name} DSS Component Heatmap")

volume = len(headlines) / 20
spread = np.std(scores)
impact = len([score for score in scores if score < -0.3]) / len(scores)
complexity = np.std([len(headline) for headline in headlines]) / 100
counter_narrative = len([score for score in scores if score > 0.3]) / len(scores)

heatmap_df = pd.DataFrame({
    "Metric": [
        "Volume",
        "Spread",
        "Impact",
        "Complexity",
        "CounterNarrative",
    ],
    "Value": [
        volume,
        spread,
        impact,
        complexity,
        counter_narrative,
    ],
})

heatmap_fig = go.Figure(
    data=go.Heatmap(
        z=[heatmap_df["Value"]],
        x=heatmap_df["Metric"],
        y=[display_name],
        colorscale="Reds",
    )
)

heatmap_fig.update_layout(
    height=300,
)

st.plotly_chart(
    heatmap_fig,
    use_container_width=True,
)
