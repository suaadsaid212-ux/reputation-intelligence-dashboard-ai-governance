import streamlit as st

from utils.glossary import render_glossary
from utils.multilingual_content import (
    CONTENT_LANGUAGES,
    get_selected_content_languages,
)


st.set_page_config(
    page_title="Reputation Intelligence Platform",
    layout="wide",
)

st.title("🛡️ TrustIntel AI")

render_glossary()

st.markdown(
    """
### Multilingual Reputation, Governance & Authenticity Intelligence

TrustIntel AI combines:

- Multilingual news and narrative monitoring
- Cross-platform social intelligence
- AI governance and digital responsibility analysis
- Reputation and crisis risk scoring
- Search and financial-market signals
- Country and sector exposure
- Content authenticity and factual verification
"""
)

selected_codes = get_selected_content_languages()

language_names = [
    name
    for name, code
    in CONTENT_LANGUAGES.items()
    if code in selected_codes
]

st.subheader("Active Data Languages")

st.write(
    ", ".join(language_names)
)

st.info(
    "Use the global Data languages control in the sidebar "
    "to choose which languages TrustIntel AI collects and analyses."
)
