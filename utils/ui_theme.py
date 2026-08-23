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

        @keyframes tiScan {
            0% { transform: translateX(-110%); opacity: 0; }
            20% { opacity: .22; }
            80% { opacity: .22; }
            100% { transform: translateX(310%); opacity: 0; }
        }

        .ti-verdict {
            position: relative;
            overflow: hidden;
            background: linear-gradient(135deg, rgba(255,255,255,.99), rgba(242,249,251,.98));
            border: 1px solid #dce8ee;
            border-radius: 20px;
            padding: 22px 24px;
            margin: 10px 0 20px;
            box-shadow: 0 14px 34px rgba(15,31,50,.055);
            animation: tiFadeUp .48s ease-out both;
        }

        .ti-verdict:after {
            content: "";
            position: absolute;
            top: 0;
            bottom: 0;
            width: 28%;
            background: linear-gradient(90deg, transparent, rgba(85,214,244,.18), transparent);
            animation: tiScan 4.8s ease-in-out infinite;
            pointer-events: none;
        }

        .ti-verdict-label {
            color: var(--ti-cyan);
            font-weight: 800;
            font-size: .76rem;
            letter-spacing: .11em;
            text-transform: uppercase;
            margin-bottom: 7px;
        }

        .ti-verdict-status {
            color: var(--ti-navy);
            font-size: clamp(1.8rem, 3vw, 2.7rem);
            line-height: 1.05;
            font-weight: 820;
            margin-bottom: 8px;
        }

        .ti-verdict-copy {
            color: #476477;
            line-height: 1.55;
            max-width: 980px;
        }

        .ti-workflow {
            display: flex;
            align-items: stretch;
            gap: 9px;
            flex-wrap: wrap;
            margin: 10px 0 22px;
        }

        .ti-step {
            flex: 1 1 150px;
            min-width: 0;
            background: rgba(255,255,255,.96);
            border: 1px solid var(--ti-line);
            border-radius: 14px;
            padding: 13px 14px;
            animation: tiFadeUp .5s ease-out both;
        }

        .ti-step-num {
            color: var(--ti-cyan);
            font-size: .72rem;
            font-weight: 800;
            letter-spacing: .08em;
            text-transform: uppercase;
        }

        .ti-step-title {
            color: var(--ti-navy);
            font-weight: 720;
            margin-top: 3px;
        }

        .ti-step-copy {
            color: var(--ti-muted);
            font-size: .82rem;
            line-height: 1.35;
            margin-top: 3px;
        }


        @keyframes tiThreatPulse {
            0%, 100% { box-shadow: 0 14px 34px rgba(15,31,50,.055); }
            50% { box-shadow: 0 18px 42px rgba(15,31,50,.10); }
        }

        .ti-threat {
            position: relative;
            overflow: hidden;
            background: linear-gradient(135deg, rgba(255,255,255,.99), rgba(246,249,251,.99));
            border: 1px solid #dce8ee;
            border-left: 5px solid var(--ti-cyan);
            border-radius: 20px;
            padding: 22px 24px;
            margin: 10px 0 20px;
            animation:
                tiFadeUp .48s ease-out both,
                tiThreatPulse 3.4s ease-in-out infinite;
        }

        .ti-threat-kicker {
            color: var(--ti-cyan);
            font-weight: 800;
            font-size: .76rem;
            letter-spacing: .11em;
            text-transform: uppercase;
            margin-bottom: 7px;
        }

        .ti-threat-level {
            color: var(--ti-navy);
            font-size: clamp(1.8rem, 3vw, 2.65rem);
            line-height: 1.05;
            font-weight: 820;
            margin-bottom: 8px;
        }

        .ti-threat-copy {
            color: #476477;
            line-height: 1.55;
            max-width: 980px;
        }

        .ti-response-grid {
            display: grid;
            grid-template-columns: repeat(3, minmax(0, 1fr));
            gap: 10px;
            margin: 10px 0 20px;
        }

        .ti-response-card {
            background: rgba(255,255,255,.96);
            border: 1px solid var(--ti-line);
            border-radius: 15px;
            padding: 15px 16px;
            animation: tiFadeUp .5s ease-out both;
        }

        .ti-response-title {
            color: var(--ti-navy);
            font-weight: 740;
            margin-bottom: 4px;
        }

        .ti-response-copy {
            color: var(--ti-muted);
            font-size: .86rem;
            line-height: 1.4;
        }

        @media (max-width: 850px) {
            .ti-response-grid {
                grid-template-columns: 1fr;
            }
        }


        .ti-statusbar {
            display: flex;
            align-items: center;
            justify-content: space-between;
            gap: 12px;
            flex-wrap: wrap;
            background: rgba(255,255,255,.92);
            border: 1px solid var(--ti-line);
            border-radius: 14px;
            padding: 10px 12px;
            margin: 4px 0 10px;
            box-shadow: 0 8px 22px rgba(15,31,50,.04);
            animation: tiFadeIn .4s ease-out both;
        }

        .ti-status-left {
            display: flex;
            align-items: center;
            gap: 8px;
            flex-wrap: wrap;
            min-width: 0;
        }

        .ti-status-title {
            color: var(--ti-navy);
            font-size: .84rem;
            font-weight: 760;
            margin-right: 3px;
        }

        .ti-source-pill {
            display: inline-flex;
            align-items: center;
            gap: 6px;
            padding: 4px 6px 4px 8px;
            border: 1px solid #E2E8F0;
            border-radius: 999px;
            background: #FFFFFF;
        }

        .ti-source-name {
            color: #475569;
            font-size: .72rem;
            font-weight: 650;
        }

        .ti-source-status {
            padding: 2px 6px;
            border-radius: 999px;
            font-size: .65rem;
            line-height: 1.25;
            font-weight: 820;
            letter-spacing: .03em;
        }

        .ti-status-time {
            color: #64748B;
            font-size: .72rem;
            white-space: nowrap;
        }

        .ti-status-note {
            color: #64748B;
            font-size: .76rem;
            line-height: 1.45;
            margin: -2px 2px 12px;
        }

        .ti-feed-card {
            background: rgba(255,255,255,.96);
            border: 1px solid var(--ti-line);
            border-radius: 16px;
            padding: 16px 17px;
            min-height: 124px;
            box-shadow: 0 9px 26px rgba(15,31,50,.045);
            animation: tiFadeUp .45s ease-out both;
        }

        .ti-feed-kicker {
            color: var(--ti-cyan);
            font-size: .72rem;
            font-weight: 800;
            letter-spacing: .09em;
            text-transform: uppercase;
            margin-bottom: 5px;
        }

        .ti-feed-value {
            color: var(--ti-navy);
            font-size: 1.55rem;
            font-weight: 810;
            line-height: 1.08;
            margin-bottom: 4px;
        }

        .ti-feed-copy {
            color: var(--ti-muted);
            font-size: .82rem;
            line-height: 1.38;
        }

        .ti-feed-alert {
            background:
                linear-gradient(
                    120deg,
                    rgba(255,255,255,.98),
                    rgba(240,249,250,.98),
                    rgba(255,255,255,.98)
                );
            background-size: 220% 220%;
            animation:
                tiGradient 11s ease infinite,
                tiFadeUp .45s ease-out both;
            border: 1px solid #DCE8EE;
            border-left: 4px solid var(--ti-cyan);
            border-radius: 17px;
            padding: 17px 18px;
            margin: 10px 0 18px;
        }

        </style>
        """,
        unsafe_allow_html=True,
    )
