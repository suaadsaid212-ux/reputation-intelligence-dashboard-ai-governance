import streamlit as st
from utils.multilingual_content import CONTENT_LANGUAGES, get_selected_content_languages

st.set_page_config(page_title="TrustIntel AI", page_icon="🛡️", layout="wide")

selected_codes = get_selected_content_languages()
language_names = [
    name for name, code in CONTENT_LANGUAGES.items()
    if code in selected_codes
]

st.markdown(
    '''
    <div class="ti-hero">
        <div class="ti-badge">● LIVE ENTERPRISE INTELLIGENCE MVP</div>
        <h1>TrustIntel AI</h1>
        <p>
            Decision intelligence for AI governance, reputation,
            multilingual narratives and content authenticity.
            One environment to detect risk, assess evidence and support executive action.
        </p>
        <div class="ti-strip">
            <span class="ti-pill">Multilingual Intelligence</span>
            <span class="ti-pill">AI Governance</span>
            <span class="ti-pill">Reputation Risk</span>
            <span class="ti-pill">Crisis Early Warning</span>
            <span class="ti-pill">Social & Search Signals</span>
            <span class="ti-pill">Fact Verification</span>
        </div>
    </div>
    ''',
    unsafe_allow_html=True,
)

st.markdown('<div class="ti-kicker">Decision architecture</div>', unsafe_allow_html=True)
st.subheader("From fragmented signals to an executive decision")

st.markdown(
    '''
    <div class="ti-flow">
      <div class="ti-flow-row">
        <span class="ti-node">News & Narratives</span>
        <span class="ti-node">Social Platforms</span>
        <span class="ti-node">Search Signals</span>
        <span class="ti-node">AI Governance Evidence</span>
        <span class="ti-arrow">→</span>
        <span class="ti-node">TrustIntel Intelligence Engine</span>
        <span class="ti-arrow">→</span>
        <span class="ti-node">Risk • Verification • Action</span>
      </div>
    </div>
    ''',
    unsafe_allow_html=True,
)

st.markdown('<div class="ti-kicker">Core capabilities</div>', unsafe_allow_html=True)
st.subheader("One platform. Four connected intelligence layers.")

c1, c2, c3, c4 = st.columns(4)

cards = [
    ("◎", "Reputation Intelligence",
     "Compare organizations, narratives, countries, sectors and reputation pressure in one executive view."),
    ("◈", "AI Governance Intelligence",
     "Monitor transparency, accountability, privacy, fairness, safety and responsible AI narratives."),
    ("⌁", "Omnichannel Signals",
     "Connect news, public social sources, search behaviour and multilingual evidence across markets."),
    ("✓", "Authenticity & Verification",
     "Assess source credibility, corroborating evidence, factual reliability and provenance signals."),
]

for col, (icon, title, copy) in zip([c1, c2, c3, c4], cards):
    with col:
        st.markdown(
            f'''
            <div class="ti-card">
                <div style="font-size:1.35rem;margin-bottom:8px">{icon}</div>
                <div class="ti-card-title">{title}</div>
                <div class="ti-card-copy">{copy}</div>
            </div>
            ''',
            unsafe_allow_html=True,
        )

st.markdown("")
st.markdown('<div class="ti-kicker">Active monitoring</div>', unsafe_allow_html=True)
st.subheader("Multilingual by design")

st.markdown(
    f'''
    <div class="ti-flow">
        <strong>Current data languages:</strong>
        {", ".join(language_names)}
    </div>
    ''',
    unsafe_allow_html=True,
)

st.caption("Use the global Data languages control in the sidebar to change the evidence languages collected and analysed.")
