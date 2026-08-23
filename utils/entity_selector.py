import pandas as pd
import streamlit as st

from utils.registry_utils import (
    load_registry,
)


def get_entity():
    try:
        df = load_registry()
    except FileNotFoundError:
        st.error(
            "Registry file is empty or unavailable."
        )
        st.stop()

    if df.empty:
        st.error(
            "Registry file is empty."
        )
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
        "Region",
    ]

    missing_columns = [
        column
        for column in required_columns
        if column not in df.columns
    ]

    if missing_columns:
        st.error(
            "Registry is missing required columns: "
            + ", ".join(
                missing_columns
            )
        )
        st.stop()

    entity_ids = (
        df[
            "Entity_ID"
        ]
        .dropna()
        .astype(str)
        .tolist()
    )

    preferred_id = st.session_state.get(
        "trustintel_selected_entity_id"
    )

    default_index = 0

    if preferred_id in entity_ids:
        default_index = entity_ids.index(
            preferred_id
        )

    label_map = {
        str(row["Entity_ID"]): (
            f'{row["Short_Name"]}  ·  '
            f'{str(row["Country"]).replace("_", " ")}  ·  '
            f'{row["Sector"]}'
        )
        for _, row
        in df.iterrows()
    }

    selected_id = st.sidebar.selectbox(
        "🏢 Select Organization",
        entity_ids,
        index=default_index,
        format_func=lambda value: label_map.get(
            str(value),
            str(value),
        ),
        key="trustintel_entity_selector",
    )

    st.session_state[
        "trustintel_selected_entity_id"
    ] = selected_id

    entity = df[
        df[
            "Entity_ID"
        ].astype(str).eq(
            str(
                selected_id
            )
        )
    ].iloc[0]

    return entity


def get_entity_query(
    entity,
    query_column,
    fallback_column="Short_Name",
):
    value = entity.get(
        query_column,
        "",
    )

    if (
        pd.isna(value)
        or str(value).strip() == ""
        or str(value).strip().lower() == "nan"
    ):
        value = entity.get(
            fallback_column,
            "",
        )

    if (
        pd.isna(value)
        or str(value).strip() == ""
        or str(value).strip().lower() == "nan"
    ):
        value = entity.get(
            "Entity_Name",
            "",
        )

    return str(
        value
    ).strip()
