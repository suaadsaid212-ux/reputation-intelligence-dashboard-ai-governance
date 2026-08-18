import numpy as np
import pandas as pd
import plotly.graph_objects as go
import streamlit as st
import yfinance as yf

from utils.entity_selector import (
    get_entity,
    get_entity_query,
)
from utils.glossary import metric_help, render_glossary
from utils.multilingual_content import (
    fetch_multilingual_news,
    get_selected_content_languages,
    language_coverage,
    safe_sentiment_stats,
)


st.set_page_config(
    page_title="Organization Intelligence",
    page_icon="🏢",
    layout="wide",
)

entity = get_entity()
display_name = entity["Short_Name"]
ticker = str(entity.get("Ticker", "")).strip()
news_query = get_entity_query(
    entity,
    "News_Query",
)

st.title("🏢 Organization Intelligence")
render_glossary(["DSS", "VADER"])

c1, c2, c3, c4 = st.columns(4)
c1.metric("Type", entity["Entity_Type"])
c2.metric("Country", entity["Country"])
c3.metric("Sector", entity["Sector"])
c4.metric("Priority", entity["Priority"])

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
        limit_per_language=8,
    )


@st.cache_data(ttl=3600, show_spinner=False)
def load_stock(
    ticker,
    start_date,
):
    if (
        not ticker
        or ticker.lower() == "nan"
    ):
        return pd.DataFrame()

    try:
        return yf.download(
            ticker,
            start=start_date,
            progress=False,
            auto_adjust=True,
        )
    except Exception:
        return pd.DataFrame()


stock = load_stock(
    ticker,
    start_dates[time_range],
)

if not stock.empty:
    stock["Returns"] = (
        stock["Close"].pct_change()
    )

    st.subheader(
        f"{display_name} Stock Performance"
    )

    close = stock["Close"].squeeze()

    fig = go.Figure(
        go.Scatter(
            x=close.index,
            y=close.values,
            mode="lines",
            name=display_name,
        )
    )

    fig.update_layout(
        height=450,
        xaxis_title="Date",
        yaxis_title="Adjusted Close",
    )

    st.plotly_chart(
        fig,
        use_container_width=True,
    )

st.subheader(
    f"{display_name} Multilingual News & Sentiment"
)

with st.spinner(
    "Collecting multilingual evidence..."
):
    news_df = load_news(
        news_query,
        tuple(content_languages),
    )

if news_df.empty:
    st.warning(
        "No multilingual news data found for this entity."
    )
    st.stop()

st.dataframe(
    news_df[
        [
            "Headline",
            "Language",
            "Edition Country",
            "Source",
            "Sentiment",
            "Sentiment Label",
            "Sentiment Method",
            "Sentiment Confidence",
            "Published",
            "Link",
        ]
    ],
    use_container_width=True,
    hide_index=True,
)

stats = safe_sentiment_stats(
    news_df
)

dss = stats["abs_mean"]
sentiment_volatility = stats["std"]
reputation_risk = min(
    100.0,
    (
        0.6 * sentiment_volatility
        + 0.4 * dss
    ) * 100,
)

m1, m2, m3, m4 = st.columns(4)
m1.metric(
    "DSS",
    round(dss, 3),
    help=metric_help("DSS"),
)
m2.metric(
    "Sentiment Volatility",
    round(
        sentiment_volatility,
        3,
    ),
)
m3.metric(
    "Reputation Risk",
    round(
        reputation_risk,
        2,
    ),
)
m4.metric(
    "Languages Observed",
    int(
        news_df[
            "Language"
        ].nunique()
    ),
)

st.subheader(
    "Language Coverage"
)

coverage_df = language_coverage(
    news_df
)

st.dataframe(
    coverage_df,
    use_container_width=True,
    hide_index=True,
)

left, right = st.columns(2)

with left:
    st.bar_chart(
        coverage_df.set_index(
            "Language"
        )["Narratives"]
    )

with right:
    sentiment_counts = (
        news_df[
            "Sentiment Label"
        ]
        .value_counts()
        .rename_axis("Sentiment")
        .reset_index(
            name="Narratives"
        )
    )

    pie = go.Figure(
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

    pie.update_layout(
        height=420,
    )

    st.plotly_chart(
        pie,
        use_container_width=True,
    )

st.subheader(
    "Most Negative Narratives"
)

st.dataframe(
    news_df.sort_values(
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
    ].head(15),
    use_container_width=True,
    hide_index=True,
)

st.info(
    "Headlines remain in their original language. "
    "TrustIntel AI records both the content language and the "
    "Google News edition used to retrieve it."
)
