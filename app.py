import streamlit as st

from utils.glossary import render_glossary


st.set_page_config(
    page_title="Reputation Intelligence Platform",
    layout="wide",
)

st.title("Reputation Intelligence Platform")

render_glossary()

st.markdown("""
### Real-Time Reputation Monitoring & Strategic Intelligence

This platform monitors organizations using:

- Organization registry data
- News sentiment and narrative risk
- AI governance and digital responsibility narrative filtering
- Financial market indicators
- Google Trends search intelligence
- Social media intelligence
- Crisis early warning signals
- Sector and country exposure analysis
""")

st.subheader("Platform Modules")

modules = [
    "Executive Overview",
    "Organization Intelligence",
    "Country Exposure",
    "Narrative Intelligence",
    "Sentiment & Subjectivity",
    "AI Governance & Reputation Intelligence",
    "Google Trends Intelligence",
    "Social Media Intelligence",
    "Organization Registry",
    "Lifecycle Intelligence",
    "Crisis Early Warning",
    "Sector Intelligence",
]

for module in modules:
    st.write(f"- {module}")

st.info("""
Use the sidebar navigation to open each intelligence module.
""")
