import streamlit as st
import pandas as pd
from utils.glossary import render_glossary

st.set_page_config(
    page_title="Organization Registry",
    page_icon="🏢",
    layout="wide",
)

st.title("🏢 Organization Registry")

render_glossary(["CIK"])

try:
    df = pd.read_csv(
        "config/entity_registry.csv",
        encoding="utf-8-sig",
    )
except FileNotFoundError:
    st.error("Registry file not found: config/entity_registry.csv")
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

col1, col2, col3, col4 = st.columns(4)

col1.metric("Entities", len(df))
col2.metric("Countries", df["Country"].nunique())
col3.metric("Entity Types", df["Entity_Type"].nunique())
col4.metric("Sectors", df["Sector"].nunique())

st.divider()

search = st.text_input("🔍 Search Entity")

filtered = df.copy()

if search:
    search_columns = [
        "Entity_Name",
        "Short_Name",
        "News_Query",
        "Google_Trends_Query",
        "Search_Query",
        "YouTube_Query",
        "Country",
        "Sector",
    ]

    search_mask = pd.Series(False, index=filtered.index)

    for column in search_columns:
        search_mask = search_mask | filtered[column].astype(str).str.contains(
            search,
            case=False,
            na=False,
        )

    filtered = filtered[search_mask]

st.subheader("Registry")

st.dataframe(
    filtered,
    use_container_width=True,
)

if len(filtered) > 0:
    selected = st.selectbox(
        "Select Entity",
        filtered["Entity_Name"],
    )

    profile = filtered[
        filtered["Entity_Name"] == selected
    ].iloc[0]

    st.subheader("Entity Profile")

    p1, p2, p3, p4 = st.columns(4)

    p1.metric("Short Name", profile["Short_Name"])
    p2.metric("Type", profile["Entity_Type"])
    p3.metric("Country", profile["Country"])
    p4.metric("Priority", profile["Priority"])

    st.write("**Entity ID:**", profile["Entity_ID"])
    st.write("**Entity Name:**", profile["Entity_Name"])
    st.write("**Ticker:**", profile["Ticker"])
    st.write("**Sector:**", profile["Sector"])
    st.write("**Industry:**", profile["Industry"])
    st.write("**Data Source Type:**", profile["Data_Source_Type"])

    st.subheader("Real Data Lookup Fields")

    st.write("**News Query:**", profile["News_Query"])
    st.write("**Google Trends Query:**", profile["Google_Trends_Query"])
    st.write("**Search Query:**", profile["Search_Query"])
    st.write("**YouTube Query:**", profile["YouTube_Query"])
    st.write("**CIK:**", profile["CIK"])

    website = str(profile["Website"]).strip()

    if website and website.lower() != "nan":
        st.link_button("Open Official Website", website)

else:
    st.info("No matching entities found.")
