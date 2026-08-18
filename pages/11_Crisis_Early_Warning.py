import pandas as pd
import plotly.graph_objects as go
import streamlit as st

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
    page_title="Crisis Early Warning",
    page_icon="🚨",
    layout="wide",
)

entity = get_entity()

entity_name = entity["Entity_Name"]
display_name = entity["Short_Name"]
news_query = get_entity_query(
    entity,
    "News_Query",
)
trends_query = get_entity_query(
    entity,
    "Google_Trends_Query",
)
youtube_query = get_entity_query(
    entity,
    "YouTube_Query",
)

priority = entity["Priority"]
ticker = str(
    entity.get(
        "Ticker",
        "",
    )
).strip()
cik = str(
    entity.get(
        "CIK",
        "",
    )
).strip()

st.title(
    "🚨 Crisis Early Warning"
)

render_glossary(
    [
        "RII",
        "OLI",
        "SRI",
    ]
)

st.markdown(
    f"""
### Crisis Monitoring & Early Detection

**Selected Entity:** {display_name}

This module now monitors crisis-relevant narratives
across the selected data languages rather than one
US English news edition.
"""
)

c1, c2, c3, c4 = st.columns(4)
c1.metric(
    "Type",
    entity["Entity_Type"],
)
c2.metric(
    "Country",
    entity["Country"],
)
c3.metric(
    "Sector",
    entity["Sector"],
)
c4.metric(
    "Priority",
    priority,
)

content_languages = (
    get_selected_content_languages()
)


def has_value(value):
    text = str(value).strip()
    return (
        bool(text)
        and text.lower() != "nan"
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
    "Scanning multilingual crisis narratives..."
):
    news_df = load_news(
        news_query,
        tuple(content_languages),
    )

stats = safe_sentiment_stats(
    news_df
)

if stats["count"]:
    news_risk = round(
        min(
            100.0,
            (
                min(
                    1.0,
                    stats["count"]
                    / max(
                        25,
                        len(
                            content_languages
                        ) * 8,
                    ),
                )
                * 35
                + stats[
                    "negative_ratio"
                ]
                * 45
                + stats[
                    "std"
                ]
                * 20
            ),
        ),
        2,
    )
else:
    news_risk = 20.0

search_risk = (
    65
    if has_value(
        trends_query
    )
    else 35
)

social_risk = (
    60
    if has_value(
        youtube_query
    )
    else 35
)

priority_risk = {
    "Critical": 75,
    "High": 60,
    "Medium": 45,
    "Low": 30,
}.get(
    priority,
    45,
)

financial_risk = (
    65
    if (
        has_value(ticker)
        or has_value(cik)
    )
    else 40
)

rii_risk = round(
    min(
        100.0,
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
        0.0,
        100
        - (
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

st.subheader(
    "Executive Risk Overview"
)

k1, k2, k3, k4, k5 = st.columns(5)

k1.metric(
    "News Risk",
    news_risk,
)
k2.metric(
    "Social Risk",
    social_risk,
)
k3.metric(
    "Search Risk",
    search_risk,
)
k4.metric(
    "RII Risk",
    rii_risk,
    help=metric_help("RII"),
)
k5.metric(
    "OLI Risk",
    oli_risk,
    help=metric_help("OLI"),
)

st.success(
    f"Current Alert Level: {level}"
)

gauge = go.Figure(
    go.Indicator(
        mode="gauge+number",
        value=crisis_score,
        title={
            "text":
            "Crisis Risk Score"
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

risk_df = pd.DataFrame(
    {
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
    }
)

st.subheader(
    "Risk Breakdown"
)

st.bar_chart(
    risk_df.set_index(
        "Risk Source"
    )["Score"]
)

st.subheader(
    "Multilingual Crisis Coverage"
)

if not news_df.empty:
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
    "Latest Crisis-Relevant Headlines"
)

if news_df.empty:
    st.info(
        "No live multilingual news headlines found for this entity."
    )
else:
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
                "Sentiment Label",
                "Sentiment Confidence",
                "Published",
                "Link",
            ]
        ].head(30),
        use_container_width=True,
        hide_index=True,
    )

st.subheader(
    "Recommended Actions"
)

if crisis_score > 80:
    st.error(
        """
Immediate action required.

- Activate crisis response team
- Increase multilingual media monitoring
- Prepare stakeholder response
- Review narrative escalation by language and region
"""
    )
elif crisis_score > 60:
    st.warning(
        """
Elevated monitoring recommended.

- Monitor multilingual social sentiment
- Review search activity
- Track news developments by language
"""
    )
else:
    st.info(
        """
Situation currently stable.

Continue standard multilingual monitoring.
"""
    )

st.info(
    f"""
Entity: {display_name}

Internal Entity Name: {entity_name}

Crisis Score: {crisis_score}

Alert Level: {level}

Languages observed: {
    int(news_df["Language"].nunique())
    if not news_df.empty
    else 0
}
"""
)
