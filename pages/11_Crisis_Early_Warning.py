import streamlit as st
import pandas as pd
import plotly.graph_objects as go
import feedparser

from vaderSentiment.vaderSentiment import SentimentIntensityAnalyzer
from urllib.parse import quote_plus

from utils.entity_selector import get_entity, get_entity_query
from utils.glossary import metric_help, render_glossary

st.set_page_config(
    page_title="Crisis Early Warning",
    page_icon="🚨",
    layout="wide",
)

entity = get_entity()

entity_name = entity["Entity_Name"]
display_name = entity["Short_Name"]
news_query = get_entity_query(entity, "News_Query")
trends_query = get_entity_query(entity, "Google_Trends_Query")
youtube_query = get_entity_query(entity, "YouTube_Query")

priority = entity["Priority"]
entity_type = entity["Entity_Type"]
ticker = str(entity.get("Ticker", "")).strip()
cik = str(entity.get("CIK", "")).strip()

st.title("🚨 Crisis Early Warning")

render_glossary(["RII", "OLI", "SRI"])

st.markdown(f"""
### Crisis Monitoring & Early Detection

**Selected Entity:** {display_name}

This module identifies emerging reputation threats,
narrative escalation, search spikes, and social pressure.
""")

c1, c2, c3, c4 = st.columns(4)

c1.metric("Type", entity_type)
c2.metric("Country", entity["Country"])
c3.metric("Sector", entity["Sector"])
c4.metric("Priority", priority)

st.caption(f"News query: {news_query}")

st.divider()


def has_value(value):
    text = str(value).strip()
    return bool(text) and text.lower() != "nan"


@st.cache_data(ttl=1800)
def get_news_headlines(query):
    encoded_query = quote_plus(query)

    feed = feedparser.parse(
        f"https://news.google.com/rss/search?q={encoded_query}&hl=en-US&gl=US&ceid=US:en"
    )

    return [
        entry.title
        for entry in feed.entries[:25]
    ]


analyzer = SentimentIntensityAnalyzer()

headlines = get_news_headlines(news_query)

sentiment_scores = [
    analyzer.polarity_scores(headline)["compound"]
    for headline in headlines
]

if sentiment_scores:
    negative_ratio = len(
        [score for score in sentiment_scores if score <= -0.3]
    ) / len(sentiment_scores)

    sentiment_volatility = pd.Series(sentiment_scores).std()

    news_risk = round(
        min(
            100,
            (
                len(headlines) / 25 * 35
                + negative_ratio * 45
                + sentiment_volatility * 20
            ),
        ),
        2,
    )
else:
    negative_ratio = 0
    sentiment_volatility = 0
    news_risk = 20

search_risk = 65 if has_value(trends_query) else 35
social_risk = 60 if has_value(youtube_query) else 35

priority_risk = {
    "Critical": 75,
    "High": 60,
    "Medium": 45,
    "Low": 30,
}.get(priority, 45)

financial_risk = 65 if has_value(ticker) or has_value(cik) else 40

rii_risk = round(
    min(
        100,
        (
            news_risk * 0.50
            + financial_risk * 0.25
            + priority_risk * 0.25
        ),
    ),
    2,
)

oli_risk = round(
    max(
        0,
        100 - (
            priority_risk * 0.40
            + search_risk * 0.25
            + social_risk * 0.20
            + financial_risk * 0.15
        ),
    ),
    2,
)

crisis_score = round(
    (
        news_risk * 0.35
        + social_risk * 0.20
        + search_risk * 0.20
        + rii_risk * 0.15
        + oli_risk * 0.10
    ),
    2,
)

if crisis_score <= 20:
    level = "🟢 Normal"
elif crisis_score <= 40:
    level = "🟡 Watch"
elif crisis_score <= 60:
    level = "🟠 Elevated"
elif crisis_score <= 80:
    level = "🔴 High Risk"
else:
    level = "🚨 Crisis Alert"

st.subheader("Executive Risk Overview")

k1, k2, k3, k4, k5 = st.columns(5)

k1.metric("News Risk", news_risk, help="Risk signal from news volume, negative sentiment ratio, and sentiment volatility.")
k2.metric("Social Risk", social_risk, help="Prototype social-media readiness/risk signal from available social fields.")
k3.metric("Search Risk", search_risk, help="Prototype search-readiness risk signal based on Google Trends query availability.")
k4.metric("RII Risk", rii_risk, help=metric_help("RII"))
k5.metric("OLI Risk", oli_risk, help=metric_help("OLI"))

st.success(f"Current Alert Level: {level}")

gauge = go.Figure(
    go.Indicator(
        mode="gauge+number",
        value=crisis_score,
        title={"text": "Crisis Risk Score"},
        gauge={
            "axis": {
                "range": [0, 100],
            },
        },
    )
)

st.plotly_chart(gauge, use_container_width=True)

st.subheader("Risk Breakdown")

risk_df = pd.DataFrame({
    "Risk Source": [
        "News",
        "Social",
        "Search",
        "RII",
        "OLI",
    ],
    "Score": [
        news_risk,
        social_risk,
        search_risk,
        rii_risk,
        oli_risk,
    ],
})

bar_fig = go.Figure()

bar_fig.add_trace(
    go.Bar(
        x=risk_df["Risk Source"],
        y=risk_df["Score"],
        text=risk_df["Score"],
        textposition="auto",
    )
)

bar_fig.update_layout(
    height=500,
    yaxis_title="Risk Score",
)

st.plotly_chart(bar_fig, use_container_width=True)

st.subheader("Threat Matrix")

matrix_df = pd.DataFrame({
    "Threat": [
        "Negative News",
        "Search Spike",
        "Social Pressure",
        "Narrative Escalation",
        "Financial / Institutional Exposure",
    ],
    "Probability": [
        round(news_risk, 2),
        round(search_risk, 2),
        round(social_risk, 2),
        round((news_risk + social_risk) / 2, 2),
        round(financial_risk, 2),
    ],
})

st.dataframe(
    matrix_df,
    use_container_width=True,
    hide_index=True,
)

st.subheader("Latest Crisis-Relevant Headlines")

if headlines:
    headline_df = pd.DataFrame({
        "Headline": headlines,
        "Sentiment": sentiment_scores,
    })

    st.dataframe(
        headline_df,
        use_container_width=True,
        hide_index=True,
    )
else:
    st.info("No live news headlines found for this entity.")

st.subheader("Recommended Actions")

if crisis_score > 80:
    st.error("""
Immediate action required.

- Activate crisis response team
- Increase media monitoring
- Prepare stakeholder response
- Review narrative escalation
""")

elif crisis_score > 60:
    st.warning("""
Elevated monitoring recommended.

- Monitor social sentiment
- Review search activity
- Track news developments
""")

else:
    st.info("""
Situation currently stable.

Continue standard monitoring.
""")

st.info(f"""
Entity: {display_name}

Internal Entity Name: {entity_name}

Crisis Score: {crisis_score}

Alert Level: {level}

Current model uses:

- Live Google News RSS headlines
- Registry-based search readiness
- Registry-based social readiness
- Priority and financial identifier exposure

Future versions will connect directly to:

- Google Trends metrics
- YouTube and Reddit APIs
- Shared RII score storage
- Shared OLI score storage
- Reputation Forecasting
""")
