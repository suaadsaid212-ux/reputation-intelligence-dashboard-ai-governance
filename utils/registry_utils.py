from pathlib import Path

import pandas as pd
import streamlit as st


BASE_REGISTRY_PATH = Path("config/entity_registry.csv")
EXPANSION_REGISTRY_PATH = Path("config/entity_registry_expansion.csv")
PORTFOLIO_PATH = Path("config/entity_portfolios.csv")


REGION_BY_COUNTRY = {
    "Oman": "GCC",
    "Saudi_Arabia": "GCC",
    "United_Arab_Emirates": "GCC",
    "Qatar": "GCC",
    "Kuwait": "GCC",
    "Bahrain": "GCC",
    "USA": "North America",
    "Canada": "North America",
    "Mexico": "Latin America",
    "Brazil": "Latin America",
    "United_Kingdom": "UK",
    "Russia": "Russia / CIS",
    "Kazakhstan": "Russia / CIS",
    "China": "East Asia",
    "Japan": "East Asia",
    "South_Korea": "East Asia",
    "India": "South Asia",
    "Singapore": "Southeast Asia",
    "Malaysia": "Southeast Asia",
    "Indonesia": "Southeast Asia",
    "Australia": "Oceania",
    "New_Zealand": "Oceania",
    "Switzerland": "Europe",
    "Germany": "Europe",
    "France": "Europe",
    "Italy": "Europe",
    "Spain": "Europe",
    "Portugal": "Europe",
    "Netherlands": "Europe",
    "Belgium": "Europe",
    "Austria": "Europe",
    "Sweden": "Europe",
    "Norway": "Europe",
    "Denmark": "Europe",
    "Finland": "Europe",
    "Poland": "Europe",
    "Ukraine": "Europe",
    "Global": "Global",
}


def infer_region(country):
    country = str(country or "").strip()

    if country in REGION_BY_COUNTRY:
        return REGION_BY_COUNTRY[country]

    if not country or country.lower() == "nan":
        return "Unknown"

    return "Other"


def _read_csv_if_exists(path):
    path = Path(path)

    if not path.exists():
        return pd.DataFrame()

    return pd.read_csv(
        path,
        encoding="utf-8-sig",
    )


@st.cache_data(ttl=300)
def load_registry():
    base = _read_csv_if_exists(
        BASE_REGISTRY_PATH
    )

    if base.empty:
        raise FileNotFoundError(
            "Registry file not found: config/entity_registry.csv"
        )

    expansion = _read_csv_if_exists(
        EXPANSION_REGISTRY_PATH
    )

    frames = [
        base
    ]

    if not expansion.empty:
        frames.append(
            expansion
        )

    registry = pd.concat(
        frames,
        ignore_index=True,
        sort=False,
    )

    registry = registry.drop_duplicates(
        subset=[
            "Entity_ID",
        ],
        keep="last",
    ).reset_index(
        drop=True
    )

    if "Region" not in registry.columns:
        registry[
            "Region"
        ] = registry[
            "Country"
        ].map(
            infer_region
        )
    else:
        registry[
            "Region"
        ] = registry[
            "Region"
        ].fillna(
            registry[
                "Country"
            ].map(
                infer_region
            )
        )

    registry[
        "Display_Name"
    ] = (
        registry[
            "Entity_Name"
        ]
        .astype(str)
        .str.replace(
            "_",
            " ",
            regex=False,
        )
    )

    return registry


@st.cache_data(ttl=300)
def load_portfolio_memberships():
    memberships = _read_csv_if_exists(
        PORTFOLIO_PATH
    )

    if memberships.empty:
        return pd.DataFrame(
            columns=[
                "Portfolio",
                "Description",
                "Entity_ID",
            ]
        )

    return memberships.drop_duplicates(
        subset=[
            "Portfolio",
            "Entity_ID",
        ]
    ).reset_index(
        drop=True
    )


def portfolio_catalog():
    memberships = load_portfolio_memberships()

    if memberships.empty:
        return pd.DataFrame(
            columns=[
                "Portfolio",
                "Description",
                "Organizations",
            ]
        )

    return (
        memberships.groupby(
            [
                "Portfolio",
                "Description",
            ],
            as_index=False,
        )
        .agg(
            Organizations=(
                "Entity_ID",
                "nunique",
            )
        )
        .sort_values(
            [
                "Portfolio",
            ]
        )
        .reset_index(
            drop=True
        )
    )


def portfolio_entity_ids(portfolio):
    memberships = load_portfolio_memberships()

    if (
        memberships.empty
        or not portfolio
        or portfolio == "All portfolios"
    ):
        return []

    return (
        memberships.loc[
            memberships[
                "Portfolio"
            ].eq(
                portfolio
            ),
            "Entity_ID",
        ]
        .dropna()
        .astype(str)
        .unique()
        .tolist()
    )


def portfolio_names():
    catalog = portfolio_catalog()

    if catalog.empty:
        return []

    return catalog[
        "Portfolio"
    ].tolist()
