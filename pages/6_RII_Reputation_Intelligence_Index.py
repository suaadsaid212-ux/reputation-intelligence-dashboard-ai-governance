import numpy as np
import pandas as pd
import plotly.graph_objects as go
import streamlit as st
import yfinance as yf

from utils.entity_selector import get_entity, get_entity_query
from utils.glossary import metric_help, render_glossary
from utils.multilingual_content import (
    fetch_multilingual_news,
    get_selected_content_languages,
    language_coverage,
    safe_sentiment_stats,
)


st.set_page_config(
    page_title="RII Reputation Intelligence Index",
    page_icon="🏆",
    layout="wide",
)

entity = get_entity()

entity_name = entity["Entity_Name"]
display_name = entity["Short_Name"]
entity_type = entity["Entity_Type"]
ticker = str(entity.get("Ticker", "")).strip()
news_query = get_entity_query(
    entity,
    "News_Query",
)

st.title(
    "🏆 Reputation Intelligence Index (RII)"
)

render_glossary(["RII", "VADER"])

st.markdown(
    f"""
### Reputation Risk Assessment

**Selected Entity:** {display_name}

RII measures organizational reputation pressure using
multilingual exposure, vulnerability, resilience, and
financial volatility where available.
"""
)

c1, c2, c3, c4 = st.columns(4)
c1.metric("Type", entity["Entity_Type"])
c2.metric("Country", entity["Country"])
c3.metric("Sector", entity["Sector"])
c4.metric("Priority", entity["Priority"])

start_date = st.sidebar.selectbox(
    "Analysis Period",
    [
        "2025-01-01",
        "2024-01-01",
        "2023-01-01",
        "2021-01-01",
    ],
)

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


with st.spinner(
    "Collecting multilingual RII evidence..."
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

stats = safe_sentiment_stats(
    news_df
)

financial_volatility = 0.0

if (
    entity_type == "Company"
    and ticker
    and ticker.lower() != "nan"
):
    try:
        stock = yf.download(
            ticker,
            start=start_date,
            progress=False,
            auto_adjust=True,
        )

        if not stock.empty:
            stock["Returns"] = (
                stock["Close"].pct_change()
            )
            value = stock[
                "Returns"
            ].std()

            try:
                financial_volatility = float(
                    value
                )
            except Exception:
                financial_volatility = float(
                    value.squeeze()
                )
    except Exception:
        financial_volatility = 0.0

news_volume = stats["count"]
negative_ratio = stats[
    "negative_ratio"
]
positive_ratio = stats[
    "positive_ratio"
]
sentiment_volatility = stats[
    "std"
]

english_subjectivity = (
    news_df.loc[
        news_df[
            "Language Code"
        ].eq("en"),
        "Subjectivity",
    ]
    .dropna()
)

avg_subjectivity = (
    float(
        english_subjectivity.mean()
    )
    if not english_subjectivity.empty
    else 0.5
)

target_volume = max(
    25,
    len(content_languages) * 8,
)

exposure_score = min(
    100.0,
    (
        news_volume
        / target_volume
    )
    * 100,
)

vulnerability_score = min(
    100.0,
    (
        negative_ratio * 40
        + sentiment_volatility * 30
        + avg_subjectivity * 20
        + financial_volatility * 100
    ),
)

resilience_score = min(
    100.0,
    (
        positive_ratio * 50
        + max(
            0.0,
            1 - sentiment_volatility,
        ) * 30
        + (
            1 - negative_ratio
        ) * 20
    ),
)

rii = (
    0.35 * exposure_score
    + 0.35 * vulnerability_score
    - 0.30 * resilience_score
)

rii = max(
    0.0,
    min(
        100.0,
        rii,
    ),
)

if rii >= 81:
    status = "Crisis Zone"
elif rii >= 61:
    status = "High Risk"
elif rii >= 41:
    status = "Vulnerable"
elif rii >= 21:
    status = "Monitor"
else:
    status = "Stable"

st.subheader(
    "Executive Reputation KPIs"
)

k1, k2, k3, k4, k5 = st.columns(5)

k1.metric(
    "Exposure",
    round(
        exposure_score,
        2,
    ),
)
k2.metric(
    "Vulnerability",
    round(
        vulnerability_score,
        2,
    ),
)
k3.metric(
    "Resilience",
    round(
        resilience_score,
        2,
    ),
)
k4.metric(
    "RII",
    round(
        rii,
        2,
    ),
    help=metric_help("RII"),
)
k5.metric(
    "Languages",
    int(
        news_df[
            "Language"
        ].nunique()
    ),
)

st.success(
    f"Current Status: {status}"
)

gauge = go.Figure(
    go.Indicator(
        mode="gauge+number",
        value=rii,
        title={
            "text":
            "Reputation Intelligence Index"
        },
        gauge={
            "axis": {
                "range": [
                    0,
                    100,
                ]
            }
        },
    )
)

st.plotly_chart(
    gauge,
    use_container_width=True,
)

st.subheader(
    "Multilingual RII Evidence Coverage"
)

coverage = language_coverage(
    news_df
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
    "RII Component Radar"
)

radar = go.Figure()

radar.add_trace(
    go.Scatterpolar(
        r=[
            exposure_score,
            vulnerability_score,
            resilience_score,
            rii,
        ],
        theta=[
            "Exposure",
            "Vulnerability",
            "Resilience",
            "RII",
        ],
        fill="toself",
        name=display_name,
    )
)

radar.update_layout(
    polar={
        "radialaxis": {
            "visible": True,
            "range": [
                0,
                100,
            ],
        }
    },
    height=550,
)

st.plotly_chart(
    radar,
    use_container_width=True,
)

st.subheader(
    "Latest Multilingual News Headlines"
)

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
            "Subjectivity",
            "Published",
            "Link",
        ]
    ],
    use_container_width=True,
    hide_index=True,
)

st.info(
    "RII now uses multilingual narrative volume and "
    "language-specific sentiment signals. Subjectivity remains "
    "English-validated only; where no English subjectivity exists, "
    "the model uses a neutral provisional value rather than pretending "
    "a non-English TextBlob score is valid."
)
