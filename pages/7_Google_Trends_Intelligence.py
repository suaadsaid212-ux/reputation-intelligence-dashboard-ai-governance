from pytrends.request import TrendReq
import streamlit as st
import pandas as pd
import plotly.graph_objects as go

from utils.entity_selector import get_entity, get_entity_query
from utils.glossary import metric_help, render_glossary

st.set_page_config(
    page_title="Google Trends Intelligence",
    page_icon="📈",
    layout="wide",
)

entity = get_entity()

display_name = entity["Short_Name"]
primary_entity = get_entity_query(entity, "Google_Trends_Query")

st.title("📈 Google Trends Intelligence")

render_glossary(["SRI", "RII", "OLI"])

st.markdown(f"""
### Search Intelligence Monitoring

**Selected Entity:** {display_name}

**Google Trends Query:** {primary_entity}

This module evaluates:

- Search Interest
- Search Momentum
- Search Volatility
- Geographic Exposure
- Search Risk Index (SRI)
""")

c1, c2, c3, c4 = st.columns(4)

c1.metric("Type", entity["Entity_Type"])
c2.metric("Country", entity["Country"])
c3.metric("Sector", entity["Sector"])
c4.metric("Priority", entity["Priority"])

st.divider()

comparison_input = st.sidebar.text_input(
    "Compare With (Optional)",
    "",
)

timeframe = st.sidebar.selectbox(
    "Google Trends Period",
    [
        "today 12-m",
        "today 5-y",
        "today 3-m",
        "today 1-m",
    ],
)

geo = st.sidebar.text_input(
    "Country Code (Optional)",
    "",
)

companies = [primary_entity]

if comparison_input:
    additional = [
        x.strip()
        for x in comparison_input.split(",")
        if x.strip()
    ]

    companies.extend(additional)

companies = companies[:5]


@st.cache_data(ttl=3600)
def get_google_trends_data(companies, timeframe, geo):
    pytrends = TrendReq(
        hl="en-US",
        tz=360,
        timeout=(10, 25),
    )

    pytrends.build_payload(
        companies,
        cat=0,
        timeframe=timeframe,
        geo=geo,
        gprop="",
    )

    return pytrends.interest_over_time()


@st.cache_data(ttl=3600)
def get_google_geo_data(companies, timeframe, geo):
    pytrends = TrendReq(
        hl="en-US",
        tz=360,
        timeout=(10, 25),
    )

    pytrends.build_payload(
        companies,
        cat=0,
        timeframe=timeframe,
        geo=geo,
        gprop="",
    )

    return pytrends.interest_by_region(
        resolution="COUNTRY",
        inc_low_vol=True,
        inc_geo_code=False,
    )


try:
    trends_df = get_google_trends_data(
        companies,
        timeframe,
        geo,
    )

except Exception as e:
    st.error("Google Trends data could not be loaded.")
    st.info(
        "Google Trends can temporarily block automated requests. "
        "Try one term only, wait a few minutes, or use another period."
    )
    st.code(str(e))
    st.stop()

if trends_df.empty:
    st.warning("No Google Trends data available.")
    st.stop()

if "isPartial" in trends_df.columns:
    trends_df = trends_df.drop(columns=["isPartial"])

st.subheader("Search Interest Timeline")

timeline_fig = go.Figure()

for company in companies:
    if company in trends_df.columns:
        timeline_fig.add_trace(
            go.Scatter(
                x=trends_df.index,
                y=trends_df[company],
                mode="lines",
                name=company,
            )
        )

timeline_fig.update_layout(
    height=600,
    xaxis_title="Date",
    yaxis_title="Search Interest",
)

st.plotly_chart(timeline_fig, use_container_width=True)

summary_rows = []

for company in companies:
    if company not in trends_df.columns:
        continue

    series = trends_df[company]

    avg_interest = series.mean()
    max_interest = series.max()
    volatility = series.std()

    first_value = series.iloc[0]
    last_value = series.iloc[-1]

    if first_value == 0:
        momentum = 0
    else:
        momentum = ((last_value - first_value) / first_value) * 100

    sri = (
        (0.40 * avg_interest)
        + (0.35 * volatility)
        + (0.25 * abs(momentum))
    )

    summary_rows.append({
        "Company": company,
        "Average Search Interest": round(float(avg_interest), 2),
        "Maximum Search Interest": round(float(max_interest), 2),
        "Search Volatility": round(float(volatility), 2),
        "Search Momentum %": round(float(momentum), 2),
        "Search Risk Index": round(float(sri), 2),
    })

summary_df = pd.DataFrame(summary_rows)

if summary_df.empty:
    st.warning("No summary data available.")
    st.stop()

avg_interest = round(summary_df["Average Search Interest"].mean(), 2)
avg_volatility = round(summary_df["Search Volatility"].mean(), 2)
avg_momentum = round(summary_df["Search Momentum %"].mean(), 2)
avg_sri = round(summary_df["Search Risk Index"].mean(), 2)

st.subheader("Executive Search KPIs")

k1, k2, k3, k4 = st.columns(4)

k1.metric("Avg Search Interest", avg_interest, help="Average Google Trends search interest for the selected terms.")
k2.metric("Avg Volatility", avg_volatility, help="Variation in search interest over the selected period.")
k3.metric("Avg Momentum %", avg_momentum, help="Percentage change between the first and last search-interest values.")
k4.metric("Avg SRI", avg_sri, help=metric_help("SRI"))

st.subheader("Search Intelligence Summary")

st.dataframe(summary_df, use_container_width=True)

ranking_df = summary_df.sort_values(
    by="Search Risk Index",
    ascending=False,
)

st.subheader("Search Risk Index Ranking")

st.bar_chart(
    ranking_df.set_index("Company")["Search Risk Index"]
)

st.subheader("Geographic Search Exposure")

selected_company = st.selectbox(
    "Select Entity",
    companies,
)

try:
    geo_df = get_google_geo_data(
        companies,
        timeframe,
        geo,
    )

except Exception:
    geo_df = pd.DataFrame()

if not geo_df.empty and selected_company in geo_df.columns:
    country_exposure = (
        geo_df[[selected_company]]
        .reset_index()
        .sort_values(
            by=selected_company,
            ascending=False,
        )
        .head(20)
    )

    st.dataframe(country_exposure, use_container_width=True)
else:
    st.info("No geographic search exposure data available.")

if not ranking_df.empty:
    highest = ranking_df.iloc[0]

    st.subheader("Executive Summary")

    st.info(f"""
Highest Search Risk Entity:
{highest["Company"]}

Search Risk Index:
{highest["Search Risk Index"]}

These indicators feed directly into:

- Reputation Intelligence Index (RII)
- Organizational Lifecycle Intelligence (OLI)
- Crisis Early Warning
- Narrative Risk Monitoring
""")
