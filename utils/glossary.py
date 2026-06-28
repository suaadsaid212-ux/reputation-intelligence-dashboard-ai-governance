import streamlit as st


GLOSSARY = {
    "DSS": {
        "name": "Digital Sentiment Strength",
        "definition": (
            "Average absolute sentiment intensity in the monitored news corpus. "
            "Higher values mean narratives are more emotionally loaded, whether positive or negative."
        ),
    },
    "RII": {
        "name": "Reputation Intelligence Index",
        "definition": (
            "Composite reputation-risk indicator combining exposure, vulnerability, "
            "and resilience signals. Higher values indicate stronger reputation pressure."
        ),
    },
    "OLI": {
        "name": "Organizational Lifecycle Index",
        "definition": (
            "Prototype maturity and readiness score based on entity type, priority, "
            "registry completeness, and available data fields."
        ),
    },
    "SRI": {
        "name": "Search Risk Index",
        "definition": (
            "Search-intelligence indicator combining average search interest, volatility, "
            "and momentum from Google Trends."
        ),
    },
    "SSI": {
        "name": "Social Sentiment Index",
        "definition": "Average social-media sentiment signal in the monitored social corpus.",
    },
    "SVI": {
        "name": "Social Visibility Index",
        "definition": "Estimated visibility or volume of social-media attention for the selected entity.",
    },
    "NPI": {
        "name": "Narrative Pressure Index",
        "definition": (
            "Indicator of how strongly public narratives are concentrating around "
            "an entity or issue."
        ),
    },
    "SRS": {
        "name": "Social Risk Score",
        "definition": "Composite social-media risk signal combining social sentiment, visibility, and pressure.",
    },
    "NRRI": {
        "name": "Narrative Reputation Risk Index",
        "definition": "Planned composite indicator connecting narrative risk to broader reputation-risk scoring.",
    },
    "VADER": {
        "name": "Valence Aware Dictionary and sEntiment Reasoner",
        "definition": (
            "English-oriented lexical sentiment model used for prototype polarity scoring. "
            "Arabic, Russian, and other language outputs require later validation."
        ),
    },
    "CIK": {
        "name": "Central Index Key",
        "definition": "Identifier used by the US SEC for companies and filings.",
    },
    "AI-GRS": {
        "name": "AI Governance Risk Score",
        "definition": (
            "Prototype score estimating reputation pressure in AI-governance narratives "
            "using category exposure, risk terms, and English sentiment where available."
        ),
    },
}


def metric_help(term):
    item = GLOSSARY.get(term)
    if not item:
        return None

    return f"{term}: {item['name']}. {item['definition']}"


def render_glossary(terms=None, title="Metric glossary"):
    selected_terms = terms or sorted(GLOSSARY.keys())

    if hasattr(st, "popover"):
        container = st.popover(title)
    else:
        container = st.expander(title)

    with container:
        for term in selected_terms:
            item = GLOSSARY.get(term)
            if not item:
                continue

            st.markdown(f"**{term} - {item['name']}**")
            st.write(item["definition"])
