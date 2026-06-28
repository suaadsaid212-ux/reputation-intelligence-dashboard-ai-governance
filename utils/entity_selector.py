import streamlit as st
import pandas as pd


@st.cache_data
def load_registry():
    return pd.read_csv(
        "config/entity_registry.csv",
        encoding="utf-8-sig",
    )


def get_entity():
    df = load_registry()

    if df.empty:
        st.error("Registry file is empty.")
        st.stop()

    required_columns = [
        "Entity_ID",
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
        "Search_Query",
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

    selected = st.sidebar.selectbox(
        "🏢 Select Entity",
        sorted(
            df["Entity_Name"]
            .dropna()
            .unique()
            .tolist()
        ),
    )

    entity = df[
        df["Entity_Name"] == selected
    ].iloc[0]

    return entity


def get_entity_query(entity, query_column, fallback_column="Short_Name"):
    value = entity.get(query_column, "")

    if pd.isna(value) or str(value).strip() == "" or str(value).strip().lower() == "nan":
        value = entity.get(fallback_column, "")

    if pd.isna(value) or str(value).strip() == "" or str(value).strip().lower() == "nan":
        value = entity.get("Entity_Name", "")

    return str(value).strip()
