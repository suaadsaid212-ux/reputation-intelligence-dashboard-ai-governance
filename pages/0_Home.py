import streamlit as st

from utils.multilingual_content import (
    CONTENT_LANGUAGES,
    get_selected_content_languages,
)


st.set_page_config(
    page_title="TrustIntel AI",
    page_icon="🛡️",
    layout="wide",
)

selected_codes = get_selected_content_languages()

language_names = [
    name
    for name, code
    in CONTENT_LANGUAGES.items()
    if code in selected_codes
]

st.markdown(
    """
    <div class="ti-brief" style="padding:28px 30px;border-left-width:5px;">
        <div class="ti-brief-kicker">TrustIntel AI • Enterprise Intelligence</div>
        <div style="font-size:2.15rem;font-weight:800;color:#0b1f33;line-height:1.1;margin:4px 0 10px;">
            See risk earlier. Understand why. Act with evidence.
        </div>
        <div class="ti-brief-text" style="max-width:920px;font-size:1.02rem;">
            Multilingual reputation intelligence, AI governance monitoring,
            omnichannel narrative analysis, crisis early warning and
            content verification in one decision environment.
        </div>
    </div>
    """,
    unsafe_allow_html=True,
)

m1, m2, m3, m4 = st.columns(4)

m1.metric(
    "Evidence Architecture",
    "Multi-source",
)
m2.metric(
    "Core Decision Flow",
    "Detect → Act",
)
m3.metric(
    "Data Languages",
    len(language_names),
)
m4.metric(
    "Product Stage",
    "Working MVP",
)

st.markdown(
    '<div class="ti-section-label">Platform architecture</div>',
    unsafe_allow_html=True,
)
st.subheader("Four connected intelligence layers")

c1, c2 = st.columns(2)

with c1:
    st.info(
        "📊 **Reputation & Narrative Intelligence**\n\n"
        "Organization, country and sector intelligence with multi-source "
        "narrative fusion, sentiment, reputation indices and crisis monitoring."
    )

    st.info(
        "🌐 **Omnichannel & Search Intelligence**\n\n"
        "Public social signals, platform comparison, multilingual "
        "narratives and Google search behavior."
    )

with c2:
    st.info(
        "🤖 **AI Governance Intelligence**\n\n"
        "Transparency, accountability, privacy, fairness, safety, "
        "human oversight and governance exposure."
    )

    st.info(
        "✅ **Authenticity & Verification**\n\n"
        "Source credibility, corroborating evidence, factual "
        "reliability and synthetic-content provenance signals."
    )

st.markdown(
    '<div class="ti-section-label">Active monitoring</div>',
    unsafe_allow_html=True,
)
st.subheader("Multilingual by design")

st.write(
    ", ".join(language_names)
)

st.caption(
    "Use the global Data languages control in the sidebar "
    "to select which languages TrustIntel AI collects and analyses."
)


st.markdown(
    '<div class="ti-section-label">Multi-source evidence</div>',
    unsafe_allow_html=True,
)
st.subheader("Fuse narratives instead of relying on one aggregator")

st.write(
    "Narrative Source Fusion combines Google News, GDELT and discovered or "
    "manually supplied public RSS/Atom feeds, then deduplicates and groups "
    "similar evidence into transparent narrative clusters."
)

st.page_link(
    "pages/4_Narrative_Intelligence.py",
    label="Open Narrative Source Fusion",
    icon="🧠",
)



st.markdown(
    '<div class="ti-section-label">Strategic portfolios</div>',
    unsafe_allow_html=True,
)
st.subheader("Move from organization lists to client portfolios")

st.write(
    "The Strategic Registry now organizes the monitoring universe by region, "
    "country, sector and curated portfolios such as GCC Banks, GCC Energy, "
    "GCC Telecom & Digital, Global AI Companies and International Institutions."
)

st.page_link(
    "pages/9_Organization_Registry.py",
    label="Open Strategic Registry & Portfolios",
    icon="🗂️",
)

st.markdown(
    '<div class="ti-section-label">Client-ready outputs</div>',
    unsafe_allow_html=True,
)
st.subheader("Export the exact section you need")

st.write(
    "Major client-facing charts and evidence tables now include section-level "
    "Excel and CSV downloads, plus high-resolution PNG export for Plotly charts. "
    "This lets a client move a chart or its underlying data directly into reports, "
    "presentations and further analysis."
)

st.markdown(
    '<div class="ti-section-label">Research data</div>',
    unsafe_allow_html=True,
)
st.subheader("Build a larger evidence corpus and export it")

st.write(
    "The Research Dataset workspace can collect hundreds of records across "
    "multiple organizations, sources and languages, then export the complete "
    "retained corpus and analytical summaries to a multi-sheet Excel workbook."
)

st.page_link(
    "pages/5_Sentiment_Subjectivity.py",
    label="Open Research Dataset & Export",
    icon="🧪",
)

st.markdown(
    '<div class="ti-section-label">Live operations</div>',
    unsafe_allow_html=True,
)
st.subheader("See what is changing now")

st.write(
    "Open the Live Intelligence Feed to view current multilingual signals, "
    "source freshness, refresh timestamps, and changes since the previous refresh."
)

st.page_link(
    "pages/16_Live_Intelligence_Feed.py",
    label="Open Live Intelligence Feed",
    icon="⚡",
)
