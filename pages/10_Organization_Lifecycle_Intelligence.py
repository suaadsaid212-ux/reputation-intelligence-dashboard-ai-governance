import streamlit as st
import plotly.graph_objects as go
import pandas as pd

from utils.entity_selector import get_entity, get_entity_query
from utils.glossary import metric_help, render_glossary

st.set_page_config(
    page_title="Lifecycle Intelligence",
    page_icon="🔄",
    layout="wide",
)

entity = get_entity()

entity_name = entity["Entity_Name"]
display_name = entity["Short_Name"]
entity_type = entity["Entity_Type"]
priority = entity["Priority"]
data_source_type = entity["Data_Source_Type"]

news_query = get_entity_query(entity, "News_Query")
trends_query = get_entity_query(entity, "Google_Trends_Query")
youtube_query = get_entity_query(entity, "YouTube_Query")

ticker = str(entity.get("Ticker", "")).strip()
cik = str(entity.get("CIK", "")).strip()
website = str(entity.get("Website", "")).strip()

st.title("🔄 Organization Lifecycle Intelligence")

render_glossary(["OLI", "RII", "CIK"])

st.markdown(f"""
### Organizational Lifecycle Assessment

**Selected Entity:** {display_name}

The Organizational Lifecycle Index (OLI) evaluates
the current maturity, data readiness, and strategic position of an entity.
""")

c1, c2, c3, c4 = st.columns(4)

c1.metric("Type", entity_type)
c2.metric("Country", entity["Country"])
c3.metric("Sector", entity["Sector"])
c4.metric("Priority", priority)

st.divider()


def has_value(value):
    return bool(value) and value.lower() != "nan"


base_scores = {
    "Company": 60,
    "International_Organization": 75,
    "University": 65,
    "Government": 70,
}

priority_bonus = {
    "Critical": 12,
    "High": 8,
    "Medium": 5,
    "Low": 2,
}

data_source_bonus = {
    "Financial": 10,
    "Institutional": 7,
    "Government": 8,
}

oli_components = {
    "Base Entity Maturity": base_scores.get(entity_type, 55),
    "Priority Weight": priority_bonus.get(priority, 5),
    "Data Source Strength": data_source_bonus.get(data_source_type, 5),
    "News Query Readiness": 5 if has_value(news_query) else 0,
    "Trends Query Readiness": 5 if has_value(trends_query) else 0,
    "YouTube Query Readiness": 3 if has_value(youtube_query) else 0,
    "Official Website": 4 if has_value(website) else 0,
    "Financial Identifier": 5 if has_value(ticker) or has_value(cik) else 0,
}

oli = min(
    100,
    round(
        sum(oli_components.values()),
        2,
    ),
)

if oli <= 20:
    stage = "Startup"
elif oli <= 40:
    stage = "Growth"
elif oli <= 60:
    stage = "Maturity"
elif oli <= 75:
    stage = "Recovery"
elif oli <= 90:
    stage = "Leadership"
else:
    stage = "Global Influence"

k1, k2, k3 = st.columns(3)

k1.metric("OLI Score", oli, help=metric_help("OLI"))
k2.metric("Lifecycle Stage", stage, help="Interpretive maturity stage derived from the OLI score.")
k3.metric("Data Readiness Fields", sum(1 for value in [news_query, trends_query, youtube_query, website, ticker, cik] if has_value(value)), help="Count of populated fields used for live or registry-based monitoring.")

gauge = go.Figure(
    go.Indicator(
        mode="gauge+number",
        value=oli,
        title={"text": "Organizational Lifecycle Index"},
        gauge={
            "axis": {
                "range": [0, 100],
            },
        },
    )
)

st.plotly_chart(gauge, use_container_width=True)

st.subheader("OLI Component Breakdown")

component_df = pd.DataFrame({
    "Component": list(oli_components.keys()),
    "Score": list(oli_components.values()),
})

st.dataframe(
    component_df,
    use_container_width=True,
    hide_index=True,
)

component_fig = go.Figure()

component_fig.add_trace(
    go.Bar(
        x=component_df["Component"],
        y=component_df["Score"],
        text=component_df["Score"],
        textposition="auto",
    )
)

component_fig.update_layout(
    height=500,
    yaxis_title="Contribution",
)

st.plotly_chart(component_fig, use_container_width=True)

st.subheader("Lifecycle Roadmap")

roadmap = pd.DataFrame({
    "Stage": [
        "Startup",
        "Growth",
        "Maturity",
        "Recovery",
        "Leadership",
        "Global Influence",
    ],
    "Position": [10, 30, 50, 70, 85, 100],
})

roadmap_fig = go.Figure()

roadmap_fig.add_trace(
    go.Scatter(
        x=roadmap["Position"],
        y=roadmap["Stage"],
        mode="lines+markers",
        name="Lifecycle Framework",
    )
)

roadmap_fig.add_trace(
    go.Scatter(
        x=[oli],
        y=[stage],
        mode="markers+text",
        text=[display_name],
        textposition="top center",
        marker={
            "size": 16,
            "color": "red",
        },
        name="Selected Entity",
    )
)

roadmap_fig.update_layout(
    height=500,
    xaxis_title="Lifecycle Progress",
    yaxis_title="Stage",
)

st.plotly_chart(roadmap_fig, use_container_width=True)

st.subheader("Real Data Readiness")

readiness_df = pd.DataFrame({
    "Field": [
        "News Query",
        "Google Trends Query",
        "YouTube Query",
        "Website",
        "Ticker",
        "CIK",
    ],
    "Value": [
        news_query,
        trends_query,
        youtube_query,
        website,
        ticker,
        cik,
    ],
})

readiness_df["Ready"] = readiness_df["Value"].apply(has_value)

st.dataframe(
    readiness_df,
    use_container_width=True,
    hide_index=True,
)

st.subheader("Executive Insight")

st.info(f"""
Entity: {display_name}

Internal Entity Name: {entity_name}

OLI Score: {oli}

Lifecycle Stage: {stage}

This OLI version is based on registry quality and real-data readiness.

Future versions can integrate live values from:

- RII
- Google Trends Intelligence
- Social Media Intelligence
- Crisis Early Warning
- Narrative Intelligence
""")
