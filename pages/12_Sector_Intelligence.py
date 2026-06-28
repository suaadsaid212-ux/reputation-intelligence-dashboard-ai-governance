import streamlit as st
import pandas as pd
import plotly.graph_objects as go
from utils.glossary import metric_help, render_glossary

st.set_page_config(
    page_title="Sector Intelligence",
    page_icon="🏭",
    layout="wide",
)

st.title("🏭 Sector Intelligence")

render_glossary(["RII", "OLI", "SRI", "CIK"])

st.markdown("""
Compare organizations within the same sector and identify:

- Sector Leaders
- Highest Risk Entities
- Fastest Growing Entities
- Reputation Outliers
- Competitive Positioning
""")

df = pd.read_csv(
    "config/entity_registry.csv",
    encoding="utf-8-sig",
)

required_columns = [
    "Entity_Name",
    "Short_Name",
    "Entity_Type",
    "Ticker",
    "Country",
    "Sector",
    "Industry",
    "Data_Source_Type",
    "Priority",
    "News_Query",
    "Google_Trends_Query",
    "YouTube_Query",
    "Website",
    "CIK",
]

missing_columns = [
    column
    for column in required_columns
    if column not in df.columns
]

if missing_columns:
    st.error(
        "Registry file is missing required columns: "
        + ", ".join(missing_columns)
    )
    st.stop()


def has_value(value):
    text = str(value).strip()
    return bool(text) and text.lower() != "nan"


def score_entity(row):
    priority_score = {
        "Critical": 85,
        "High": 70,
        "Medium": 50,
        "Low": 30,
    }.get(row["Priority"], 45)

    type_score = {
        "Company": 65,
        "International_Organization": 75,
        "University": 60,
        "Government": 70,
    }.get(row["Entity_Type"], 55)

    source_score = {
        "Financial": 75,
        "Institutional": 65,
        "Government": 70,
    }.get(row["Data_Source_Type"], 55)

    data_fields = [
        row["News_Query"],
        row["Google_Trends_Query"],
        row["YouTube_Query"],
        row["Website"],
        row["Ticker"],
        row["CIK"],
    ]

    readiness = sum(
        1
        for value in data_fields
        if has_value(value)
    )

    readiness_score = round(
        readiness / len(data_fields) * 100,
        2,
    )

    rii = round(
        (
            priority_score * 0.35
            + source_score * 0.25
            + readiness_score * 0.25
            + type_score * 0.15
        ),
        2,
    )

    oli = round(
        (
            type_score * 0.45
            + source_score * 0.25
            + readiness_score * 0.20
            + priority_score * 0.10
        ),
        2,
    )

    search = 75 if has_value(row["Google_Trends_Query"]) else 35
    social = 70 if has_value(row["YouTube_Query"]) else 35

    crisis = round(
        (
            priority_score * 0.40
            + rii * 0.25
            + search * 0.20
            + social * 0.15
        ),
        2,
    )

    return {
        "Entity": row["Entity_Name"],
        "Short Name": row["Short_Name"],
        "Type": row["Entity_Type"],
        "Country": row["Country"],
        "RII": rii,
        "OLI": oli,
        "Search": search,
        "Social": social,
        "Crisis": crisis,
        "Data Readiness": readiness_score,
    }


sector = st.selectbox(
    "Select Sector",
    sorted(
        df["Sector"]
        .dropna()
        .unique()
        .tolist()
    ),
)

sector_df = df[df["Sector"] == sector]

if sector_df.empty:
    st.warning("No entities found for this sector.")
    st.stop()

benchmark = [
    score_entity(row)
    for _, row in sector_df.iterrows()
]

benchmark_df = pd.DataFrame(benchmark)

st.subheader("Sector Overview")

k1, k2, k3, k4 = st.columns(4)

k1.metric("Entities", len(benchmark_df), help="Number of registry entities in the selected sector.")
k2.metric("Avg RII", round(benchmark_df["RII"].mean(), 1), help=metric_help("RII"))
k3.metric("Avg OLI", round(benchmark_df["OLI"].mean(), 1), help=metric_help("OLI"))
k4.metric("Avg Crisis", round(benchmark_df["Crisis"].mean(), 1), help="Average prototype crisis exposure score for the selected sector.")

st.subheader("Sector Benchmark")

st.dataframe(
    benchmark_df,
    use_container_width=True,
    hide_index=True,
)

st.subheader("Sector Ranking")

ranking = benchmark_df.copy()

ranking["Composite Score"] = round(
    (
        ranking["RII"] * 0.30
        + ranking["OLI"] * 0.30
        + ranking["Search"] * 0.20
        + ranking["Social"] * 0.20
    ),
    2,
)

ranking = ranking.sort_values(
    by="Composite Score",
    ascending=False,
)

st.dataframe(
    ranking[
        [
            "Entity",
            "Short Name",
            "Composite Score",
            "Data Readiness",
        ]
    ],
    use_container_width=True,
    hide_index=True,
)

st.subheader("Entity Comparison")

entities = st.multiselect(
    "Select Entities",
    benchmark_df["Entity"].tolist(),
    default=benchmark_df["Entity"].head(3).tolist(),
)

radar = go.Figure()

for selected_entity in entities:
    row = benchmark_df[
        benchmark_df["Entity"] == selected_entity
    ].iloc[0]

    radar.add_trace(
        go.Scatterpolar(
            r=[
                row["RII"],
                row["OLI"],
                row["Search"],
                row["Social"],
                row["Crisis"],
            ],
            theta=[
                "RII",
                "OLI",
                "Search",
                "Social",
                "Crisis",
            ],
            fill="toself",
            name=row["Short Name"],
        )
    )

radar.update_layout(
    height=650,
    polar=dict(
        radialaxis=dict(
            visible=True,
            range=[0, 100],
        )
    ),
)

st.plotly_chart(radar, use_container_width=True)

st.subheader("Competitive Position Matrix")

matrix = go.Figure()

matrix.add_trace(
    go.Scatter(
        x=benchmark_df["Search"],
        y=benchmark_df["RII"],
        mode="markers+text",
        text=benchmark_df["Short Name"],
        textposition="top center",
        marker={
            "size": benchmark_df["Data Readiness"] / 4 + 8,
        },
    )
)

matrix.update_layout(
    xaxis_title="Search Visibility Readiness",
    yaxis_title="Reputation Intelligence Score",
    height=600,
)

st.plotly_chart(matrix, use_container_width=True)

st.subheader("Executive Insights")

leader = ranking.iloc[0]

highest_risk = benchmark_df.sort_values(
    by="Crisis",
    ascending=False,
).iloc[0]

highest_readiness = benchmark_df.sort_values(
    by="Data Readiness",
    ascending=False,
).iloc[0]

st.success(f"Sector Leader: {leader['Short Name']}")
st.warning(f"Highest Crisis Exposure: {highest_risk['Short Name']}")
st.info(f"Best Real-Data Readiness: {highest_readiness['Short Name']}")

st.info("""
This version calculates sector intelligence from registry quality,
priority, entity type, identifiers, and real-data readiness.

Next improvement:

- connect live RII outputs
- connect live Google Trends outputs
- connect live social intelligence outputs
- store scores in a shared cache for all pages
""")
