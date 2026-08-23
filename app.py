import streamlit as st

from utils.global_i18n import (
    install_global_translation,
    language_selector,
    page_title,
)
from utils.multilingual_content import (
    content_language_selector,
)
from utils.ui_theme import (
    apply_trustintel_theme,
)


st.set_page_config(
    page_title="TrustIntel AI",
    page_icon="🛡️",
    layout="wide",
    initial_sidebar_state="expanded",
)

apply_trustintel_theme()

lang = language_selector()
content_language_selector()
install_global_translation()

pages = {
    "TrustIntel AI": [
        st.Page(
            "pages/0_Home.py",
            title=page_title("home", lang),
            icon="🏠",
            default=True,
        ),
        st.Page(
            "pages/1_Executive_Overview.py",
            title=page_title("executive", lang),
            icon="📊",
        ),
        st.Page(
            "pages/2_Organization_Intelligence.py",
            title=page_title("organization", lang),
            icon="🏢",
        ),
        st.Page(
            "pages/3_Country_Exposure.py",
            title=page_title("country", lang),
            icon="🌍",
        ),
        st.Page(
            "pages/4_Narrative_Intelligence.py",
            title=page_title("narrative", lang),
            icon="🧠",
        ),
        st.Page(
            "pages/5_Sentiment_Subjectivity.py",
            title=page_title("sentiment", lang),
            icon="💬",
        ),
        st.Page(
            "pages/6_RII_Reputation_Intelligence_Index.py",
            title=page_title("rii", lang),
            icon="🏆",
        ),
        st.Page(
            "pages/7_Google_Trends_Intelligence.py",
            title=page_title("trends", lang),
            icon="📈",
        ),
        st.Page(
            "pages/8_Social_Media_Intelligence.py",
            title=page_title("social", lang),
            icon="📣",
        ),
        st.Page(
            "pages/9_Organization_Registry.py",
            title=page_title("registry", lang),
            icon="🗂️",
        ),
        st.Page(
            "pages/10_Organization_Lifecycle_Intelligence.py",
            title=page_title("lifecycle", lang),
            icon="🔄",
        ),
        st.Page(
            "pages/11_Crisis_Early_Warning.py",
            title=page_title("crisis", lang),
            icon="🚨",
        ),
        st.Page(
            "pages/12_Sector_Intelligence.py",
            title=page_title("sector", lang),
            icon="🏭",
        ),
        st.Page(
            "pages/13_AI_Governance_Reputation_Intelligence.py",
            title=page_title("governance", lang),
            icon="🤖",
        ),
        st.Page(
            "pages/14_Omnichannel_Social_Intelligence.py",
            title=page_title("omnichannel", lang),
            icon="🌐",
        ),
        st.Page(
            "pages/15_Content_Authenticity_Fact_Verification.py",
            title=page_title("verification", lang),
            icon="✅",
        ),
    ]
}

current_page = st.navigation(
    pages,
    position="sidebar",
)

current_page.run()
