import streamlit as st
import pandas as pd
import numpy as np
import feedparser
import pydeck as pdk
import plotly.graph_objects as go

from vaderSentiment.vaderSentiment import SentimentIntensityAnalyzer
from urllib.parse import quote_plus

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
    st.error("Registry file not found: config/entity_registry.csv")
    st.stop()

required_columns = [
    "Entity_Name",
    "Short_Name",
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

coordinates = {
    "USA": [37.0902, -95.7129],
    "Russia": [61.5240, 105.3188],
    "China": [35.8617, 104.1954],
    "Japan": [36.2048, 138.2529],
    "South Korea": [35.9078, 127.7669],
    "Switzerland": [46.8182, 8.2275],
    "Global": [20.0, 0.0],
    "United_Kingdom": [55.3781, -3.4360],
    "Oman": [21.4735, 55.9754],
}

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
        filtered_registry["Country"].isin(selected_countries)
    ]

if selected_sectors:
    filtered_registry = filtered_registry[
        filtered_registry["Sector"].isin(selected_sectors)
    ]

selected_entities = st.sidebar.multiselect(
    "Select Organizations",
    filtered_registry["Entity_Name"].tolist(),
    default=filtered_registry["Entity_Name"].head(8).tolist(),
)

if not selected_entities:
    st.warning("Select at least one organization.")
    st.stop()

filtered_registry = filtered_registry[
    filtered_registry["Entity_Name"].isin(selected_entities)
]

analyzer = SentimentIntensityAnalyzer()


@st.cache_data(ttl=1800)
def get_news_scores(query):
    encoded_query = quote_plus(query)

    feed = feedparser.parse(
        f"https://news.google.com/rss/search?q={encoded_query}&hl=en-US&gl=US&ceid=US:en"
    )

    scores = []

    for entry in feed.entries[:15]:
        score = analyzer.polarity_scores(
            entry.title
        )["compound"]

        scores.append({
            "Headline": entry.title,
            "Sentiment": float(score),
        })

    return pd.DataFrame(scores)


rows = []

for _, entity in filtered_registry.iterrows():
    news_df = get_news_scores(entity["News_Query"])

    if news_df.empty:
        continue

    scores = news_df["Sentiment"].tolist()

    negative_count = len([
        score
        for score in scores
        if score <= -0.3
    ])

    dss = np.mean(np.abs(scores))
    sentiment_volatility = np.std(scores)
    reputation_risk = (
        sentiment_volatility * 60
        + dss * 40
    )

    rows.append({
        "Entity": entity["Entity_Name"],
        "Short Name": entity["Short_Name"],
        "Country": entity["Country"],
        "Sector": entity["Sector"],
        "Priority": entity["Priority"],
        "Narrative Volume": len(scores),
        "Negative Narratives": negative_count,
        "Average Sentiment": round(float(np.mean(scores)), 3),
        "Sentiment Volatility": round(float(sentiment_volatility), 3),
        "Reputation Risk": round(float(reputation_risk), 2),
    })

df = pd.DataFrame(rows)

if df.empty:
    st.error("No country exposure data available.")
    st.stop()

country_df = (
    df.groupby("Country")
    .agg({
        "Entity": "count",
        "Narrative Volume": "sum",
        "Negative Narratives": "sum",
        "Average Sentiment": "mean",
        "Sentiment Volatility": "mean",
        "Reputation Risk": "mean",
    })
    .reset_index()
)

country_df = country_df.rename(
    columns={
        "Entity": "Organizations Monitored",
        "Reputation Risk": "Average Reputation Risk",
    }
)

country_df["Average Reputation Risk"] = country_df[
    "Average Reputation Risk"
].round(2)

st.subheader("Country Exposure Summary")

st.dataframe(
    country_df,
    use_container_width=True,
    hide_index=True,
)

st.subheader("Country Risk Ranking")

ranking = country_df.sort_values(
    by="Average Reputation Risk",
    ascending=False,
)

fig = go.Figure()

fig.add_trace(
    go.Bar(
        x=ranking["Country"],
        y=ranking["Average Reputation Risk"],
        text=ranking["Average Reputation Risk"],
        textposition="auto",
    )
)

fig.update_layout(
    height=500,
    title="Average Reputation Risk by Country",
    yaxis_title="Average Reputation Risk",
)

st.plotly_chart(
    fig,
    use_container_width=True,
)

geo_rows = []

for _, row in country_df.iterrows():
    country = row["Country"]

    if country not in coordinates:
        continue

    lat, lon = coordinates[country]

    geo_rows.append({
        "Country": country,
        "Latitude": lat,
        "Longitude": lon,
        "RiskScore": row["Average Reputation Risk"],
        "Organizations": row["Organizations Monitored"],
        "NarrativeVolume": row["Narrative Volume"],
    })

geo_data = pd.DataFrame(geo_rows)

st.subheader("Geographic Country Risk Map")

if geo_data.empty:
    st.info("No geographic coordinates available for selected countries.")
else:
    layer = pdk.Layer(
        "ScatterplotLayer",
        data=geo_data,
        get_position="[Longitude, Latitude]",
        get_color="[255, 0, 0, 180]",
        get_radius="RiskScore * 50000",
        pickable=True,
    )

    view_state = pdk.ViewState(
        latitude=30,
        longitude=20,
        zoom=1,
        pitch=30,
    )

    tooltip = {
        "html":
        "<b>Country:</b> {Country}<br/>"
        "<b>Risk Score:</b> {RiskScore}<br/>"
        "<b>Organizations:</b> {Organizations}<br/>"
        "<b>Narrative Volume:</b> {NarrativeVolume}",
        "style": {
            "backgroundColor": "black",
            "color": "white",
        },
    }

    deck = pdk.Deck(
        layers=[layer],
        initial_view_state=view_state,
        tooltip=tooltip,
        map_style=None,
    )

    st.pydeck_chart(deck)

st.subheader("Organization Exposure by Country")

st.dataframe(
    df.sort_values(
        by=["Country", "Reputation Risk"],
        ascending=[True, False],
    ),
    use_container_width=True,
    hide_index=True,
)
