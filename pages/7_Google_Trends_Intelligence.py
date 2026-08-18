from pytrends.request import TrendReq

import pandas as pd
import plotly.graph_objects as go
import streamlit as st

from utils.entity_selector import get_entity, get_entity_query
from utils.glossary import metric_help, render_glossary
from utils.multilingual_content import (
    CONTENT_LANGUAGES,
    NEWS_PROFILES,
    get_selected_content_languages,
    resolve_query_alias,
)


st.set_page_config(
    page_title="Google Trends Intelligence",
    page_icon="📈",
    layout="wide",
)

entity = get_entity()

display_name = entity["Short_Name"]
primary_entity = get_entity_query(
    entity,
    "Google_Trends_Query",
)

st.title(
    "📈 Google Trends Intelligence"
)

render_glossary(
    [
        "SRI",
        "RII",
        "OLI",
    ]
)

c1, c2, c3, c4 = st.columns(4)
c1.metric("Type", entity["Entity_Type"])
c2.metric("Country", entity["Country"])
c3.metric("Sector", entity["Sector"])
c4.metric("Priority", entity["Priority"])

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

manual_compare = st.sidebar.text_input(
    "Compare With (Optional)",
    "",
)

content_languages = (
    get_selected_content_languages()
)

alias_rows = []

for code in content_languages:
    alias = resolve_query_alias(
        primary_entity,
        code,
    )

    if alias:
        alias_rows.append(
            {
                "Language":
                NEWS_PROFILES.get(
                    code,
                    {},
                ).get(
                    "label",
                    code,
                ),
                "Query Alias":
                alias,
            }
        )

alias_df = (
    pd.DataFrame(alias_rows)
    .drop_duplicates(
        subset=[
            "Query Alias"
        ]
    )
)

st.subheader(
    "Multilingual Search Aliases"
)

st.dataframe(
    alias_df,
    use_container_width=True,
    hide_index=True,
)

companies = (
    alias_df[
        "Query Alias"
    ].tolist()
    if not alias_df.empty
    else [
        primary_entity
    ]
)

if manual_compare:
    companies.extend(
        [
            item.strip()
            for item
            in manual_compare.split(",")
            if item.strip()
        ]
    )

# Google Trends comparison payload supports up to five terms.
companies = list(
    dict.fromkeys(
        companies
    )
)[:5]

if not companies:
    companies = [
        primary_entity
    ]

primary_language_code = (
    content_languages[0]
    if content_languages
    else "en"
)

hl = NEWS_PROFILES.get(
    primary_language_code,
    NEWS_PROFILES["en"],
)["hl"]


@st.cache_data(ttl=3600, show_spinner=False)
def get_google_trends_data(
    companies,
    timeframe,
    geo,
    hl,
):
    pytrends = TrendReq(
        hl=hl,
        tz=360,
        timeout=(
            10,
            25,
        ),
    )

    pytrends.build_payload(
        list(companies),
        cat=0,
        timeframe=timeframe,
        geo=geo,
        gprop="",
    )

    return (
        pytrends.interest_over_time()
    )


@st.cache_data(ttl=3600, show_spinner=False)
def get_google_geo_data(
    companies,
    timeframe,
    geo,
    hl,
):
    pytrends = TrendReq(
        hl=hl,
        tz=360,
        timeout=(
            10,
            25,
        ),
    )

    pytrends.build_payload(
        list(companies),
        cat=0,
        timeframe=timeframe,
        geo=geo,
        gprop="",
    )

    return (
        pytrends.interest_by_region(
            resolution="COUNTRY",
            inc_low_vol=True,
            inc_geo_code=False,
        )
    )


try:
    trends_df = (
        get_google_trends_data(
            tuple(companies),
            timeframe,
            geo,
            hl,
        )
    )
except Exception as error:
    st.error(
        "Google Trends data could not be loaded."
    )
    st.code(
        str(error)
    )
    st.stop()

if trends_df.empty:
    st.warning(
        "No Google Trends data available."
    )
    st.stop()

if "isPartial" in trends_df.columns:
    trends_df = trends_df.drop(
        columns=[
            "isPartial"
        ]
    )

st.subheader(
    "Search Interest Timeline"
)

timeline = go.Figure()

for company in companies:
    if company in trends_df.columns:
        timeline.add_trace(
            go.Scatter(
                x=trends_df.index,
                y=trends_df[
                    company
                ],
                mode="lines",
                name=company,
            )
        )

timeline.update_layout(
    height=560,
    xaxis_title="Date",
    yaxis_title="Search Interest",
)

st.plotly_chart(
    timeline,
    use_container_width=True,
)

summary_rows = []

for company in companies:
    if company not in trends_df:
        continue

    series = trends_df[
        company
    ]

    avg_interest = float(
        series.mean()
    )
    max_interest = float(
        series.max()
    )
    volatility = float(
        series.std()
    )

    first_value = float(
        series.iloc[0]
    )
    last_value = float(
        series.iloc[-1]
    )

    momentum = (
        (
            last_value
            - first_value
        )
        / first_value
        * 100
        if first_value
        else 0.0
    )

    sri = (
        0.40 * avg_interest
        + 0.35 * volatility
        + 0.25 * abs(
            momentum
        )
    )

    summary_rows.append(
        {
            "Query Alias":
            company,
            "Average Search Interest":
            round(
                avg_interest,
                2,
            ),
            "Maximum Search Interest":
            round(
                max_interest,
                2,
            ),
            "Search Volatility":
            round(
                volatility,
                2,
            ),
            "Search Momentum %":
            round(
                momentum,
                2,
            ),
            "Search Risk Index":
            round(
                sri,
                2,
            ),
        }
    )

summary_df = pd.DataFrame(
    summary_rows
)

st.subheader(
    "Search Intelligence Summary"
)

st.dataframe(
    summary_df,
    use_container_width=True,
    hide_index=True,
)

if not summary_df.empty:
    k1, k2, k3, k4 = st.columns(4)

    k1.metric(
        "Avg Search Interest",
        round(
            summary_df[
                "Average Search Interest"
            ].mean(),
            2,
        ),
    )

    k2.metric(
        "Avg Volatility",
        round(
            summary_df[
                "Search Volatility"
            ].mean(),
            2,
        ),
    )

    k3.metric(
        "Avg Momentum %",
        round(
            summary_df[
                "Search Momentum %"
            ].mean(),
            2,
        ),
    )

    k4.metric(
        "Avg SRI",
        round(
            summary_df[
                "Search Risk Index"
            ].mean(),
            2,
        ),
        help=metric_help("SRI"),
    )

try:
    geo_df = get_google_geo_data(
        tuple(companies),
        timeframe,
        geo,
        hl,
    )
except Exception:
    geo_df = pd.DataFrame()

st.subheader(
    "Geographic Search Exposure"
)

if geo_df.empty:
    st.info(
        "No geographic search exposure data available."
    )
else:
    st.dataframe(
        geo_df.reset_index().head(30),
        use_container_width=True,
        hide_index=True,
    )

st.info(
    "Search aliases allow TrustIntel AI to compare how the same "
    "organization is searched under local-language names. Google Trends "
    "limits one comparison payload to five terms, so the first five "
    "unique aliases are used."
)
