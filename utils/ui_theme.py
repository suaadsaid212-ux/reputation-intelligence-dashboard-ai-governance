import streamlit as st


def apply_trustintel_theme():
    st.markdown(
        """
        <style>
        :root {
            --ti-navy: #0b1f33;
            --ti-blue: #145f7a;
            --ti-cyan: #0e8fb0;
            --ti-ink: #132238;
            --ti-muted: #65758b;
            --ti-line: #e4eaf1;
            --ti-bg: #f5f8fb;
            --ti-card: #ffffff;
        }

        @keyframes tiFadeUp {
            from { opacity: 0; transform: translateY(12px); }
            to   { opacity: 1; transform: translateY(0); }
        }

        @keyframes tiFadeIn {
            from { opacity: 0; }
            to   { opacity: 1; }
        }

        @keyframes tiPulse {
            0%, 100% { opacity: 1; transform: scale(1); }
            50% { opacity: .48; transform: scale(.84); }
        }

        @keyframes tiGradient {
            0% { background-position: 0% 50%; }
            50% { background-position: 100% 50%; }
            100% { background-position: 0% 50%; }
        }

        .stApp {
            background:
                radial-gradient(circle at 92% 3%, rgba(14,143,176,.08), transparent 24rem),
                radial-gradient(circle at 2% 22%, rgba(20,95,122,.05), transparent 22rem),
                var(--ti-bg);
            color: var(--ti-ink);
        }

        [data-testid="stMainBlockContainer"] {
            padding-top: 1.35rem;
            padding-bottom: 4rem;
            max-width: 1480px;
        }

        h1, h2, h3 {
            color: var(--ti-navy);
            letter-spacing: -.02em;
        }

        h1 {
            font-weight: 780 !important;
            animation: tiFadeUp .45s ease-out both;
        }

        h2, h3 {
            font-weight: 720 !important;
        }

        /* Sidebar */
        [data-testid="stSidebar"] {
            background:
                linear-gradient(180deg, #071827 0%, #0c2940 58%, #0b314a 100%);
            border-right: 1px solid rgba(255,255,255,.08);
        }

        [data-testid="stSidebar"] * {
            color: #eaf4f8;
        }

        [data-testid="stSidebar"] [data-baseweb="select"] > div,
        [data-testid="stSidebar"] input,
        [data-testid="stSidebar"] textarea {
            background: rgba(255,255,255,.08) !important;
            border-color: rgba(255,255,255,.15) !important;
            border-radius: 10px !important;
        }

        [data-testid="stSidebarNav"] a {
            border-radius: 10px;
            margin: 2px 8px;
            padding: 8px 10px;
            transition:
                background .18s ease,
                transform .18s ease;
        }

        [data-testid="stSidebarNav"] a:hover {
            background: rgba(255,255,255,.08);
            transform: translateX(2px);
        }

        [data-testid="stSidebarNav"] a[aria-current="page"] {
            background:
                linear-gradient(
                    90deg,
                    rgba(14,143,176,.34),
                    rgba(255,255,255,.07)
                );
            box-shadow: inset 3px 0 0 #55d6f4;
        }

        /* KPI cards */
        [data-testid="stMetric"] {
            background: rgba(255,255,255,.97);
            border: 1px solid var(--ti-line);
            border-radius: 16px;
            padding: 16px 18px;
            min-height: 108px;
            box-shadow: 0 10px 28px rgba(15,31,50,.055);
            animation: tiFadeUp .52s ease-out both;
            transition:
                transform .2s ease,
                box-shadow .2s ease,
                border-color .2s ease;
        }

        [data-testid="stMetric"]:hover {
            transform: translateY(-3px);
            border-color: #cbdce5;
            box-shadow: 0 16px 34px rgba(15,31,50,.09);
        }

        [data-testid="stMetricLabel"] {
            color: var(--ti-muted) !important;
            font-weight: 640 !important;
        }

        [data-testid="stMetricValue"] {
            color: var(--ti-navy) !important;
            font-weight: 780 !important;
            letter-spacing: -.025em;
        }

        /* Cards/charts/tables */
        [data-testid="stDataFrame"],
        [data-testid="stTable"],
        [data-testid="stPlotlyChart"],
        [data-testid="stPyplot"],
        [data-testid="stDeckGlJsonChart"] {
            background: rgba(255,255,255,.97);
            border: 1px solid var(--ti-line);
            border-radius: 16px;
            padding: 8px;
            box-shadow: 0 10px 28px rgba(15,31,50,.04);
            overflow: hidden;
            animation: tiFadeIn .55s ease-out both;
        }

        [data-testid="stAlert"] {
            border-radius: 14px;
            border-width: 1px;
            animation: tiFadeUp .45s ease-out both;
        }

        [data-testid="stExpander"] {
            background: rgba(255,255,255,.86);
            border: 1px solid var(--ti-line);
            border-radius: 14px;
        }

        [data-baseweb="select"] > div,
        [data-testid="stTextInput"] input,
        [data-testid="stTextArea"] textarea {
            border-radius: 11px !important;
            border-color: #d9e3ec !important;
        }

        .stButton > button,
        .stDownloadButton > button {
            border-radius: 11px;
            font-weight: 680;
            min-height: 2.6rem;
            transition:
                transform .18s ease,
                box-shadow .18s ease;
        }

        .stButton > button:hover,
        .stDownloadButton > button:hover {
            transform: translateY(-1px);
            box-shadow: 0 8px 18px rgba(14,143,176,.13);
        }

        /* Custom lightweight animated components */
        .ti-live {
            display: inline-flex;
            align-items: center;
            gap: 8px;
            color: #476477;
            font-size: .88rem;
            margin: 2px 0 10px;
            animation: tiFadeIn .5s ease-out both;
        }

        .ti-live-dot {
            width: 8px;
            height: 8px;
            border-radius: 999px;
            background: #18a67e;
            box-shadow: 0 0 0 4px rgba(24,166,126,.10);
            animation: tiPulse 1.8s ease-in-out infinite;
        }

        .ti-brief {
            background:
                linear-gradient(
                    120deg,
                    rgba(255,255,255,.98),
                    rgba(239,248,251,.98),
                    rgba(255,255,255,.98)
                );
            background-size: 220% 220%;
            animation:
                tiGradient 10s ease infinite,
                tiFadeUp .5s ease-out both;
            border: 1px solid #dce8ee;
            border-left: 4px solid var(--ti-cyan);
            border-radius: 17px;
            padding: 18px 20px;
            margin: 8px 0 20px;
            box-shadow: 0 10px 28px rgba(15,31,50,.04);
        }

        .ti-brief-kicker {
            color: var(--ti-cyan);
            font-size: .76rem;
            font-weight: 800;
            letter-spacing: .10em;
            text-transform: uppercase;
            margin-bottom: 6px;
        }

        .ti-brief-text {
            color: #28485c;
            font-size: .96rem;
            line-height: 1.58;
        }

        .ti-section-label {
            color: var(--ti-cyan);
            font-size: .75rem;
            font-weight: 790;
            letter-spacing: .09em;
            text-transform: uppercase;
            margin-top: 10px;
            margin-bottom: -4px;
        }

        #MainMenu { visibility: hidden; }
        footer { visibility: hidden; }

        @media (prefers-reduced-motion: reduce) {
            *, *::before, *::after {
                animation-duration: .001ms !important;
                animation-iteration-count: 1 !important;
                scroll-behavior: auto !important;
                transition-duration: .001ms !important;
            }
        }
        </style>
        """,
        unsafe_allow_html=True,
    )
