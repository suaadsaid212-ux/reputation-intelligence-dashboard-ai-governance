import streamlit as st

def apply_trustintel_theme():
    st.markdown(
        '''
        <style>
        :root{
            --ti-navy:#0b1f33;
            --ti-cyan:#0e8fb0;
            --ti-ink:#132238;
            --ti-muted:#65758b;
            --ti-line:#e4eaf1;
            --ti-bg:#f5f8fb;
        }
        .stApp{
            background:
                radial-gradient(circle at 92% 3%, rgba(14,143,176,.08), transparent 24rem),
                radial-gradient(circle at 2% 22%, rgba(15,95,128,.05), transparent 22rem),
                var(--ti-bg);
            color:var(--ti-ink);
        }
        [data-testid="stMainBlockContainer"]{
            padding-top:1.4rem;
            padding-bottom:4rem;
            max-width:1480px;
        }
        h1,h2,h3{color:var(--ti-navy);letter-spacing:-.02em}
        h1{font-weight:760!important;font-size:clamp(2rem,3vw,3rem)!important}
        h2{font-weight:720!important;margin-top:1.7rem!important}
        [data-testid="stSidebar"]{
            background:linear-gradient(180deg,#071827 0%,#0c2940 58%,#0b314a 100%);
            border-right:1px solid rgba(255,255,255,.08);
        }
        [data-testid="stSidebar"] *{color:#eaf4f8}
        [data-testid="stSidebar"] [data-baseweb="select"]>div,
        [data-testid="stSidebar"] input,
        [data-testid="stSidebar"] textarea{
            background:rgba(255,255,255,.08)!important;
            border-color:rgba(255,255,255,.15)!important;
            border-radius:10px!important;
        }
        [data-testid="stSidebarNav"] a{
            border-radius:10px;
            margin:2px 8px;
            padding:8px 10px;
        }
        [data-testid="stSidebarNav"] a:hover{background:rgba(255,255,255,.08)}
        [data-testid="stSidebarNav"] a[aria-current="page"]{
            background:linear-gradient(90deg,rgba(14,143,176,.34),rgba(255,255,255,.07));
            box-shadow:inset 3px 0 0 #55d6f4;
        }
        [data-testid="stMetric"]{
            background:rgba(255,255,255,.96);
            border:1px solid var(--ti-line);
            border-radius:16px;
            padding:16px 18px;
            min-height:108px;
            box-shadow:0 10px 28px rgba(15,31,50,.055);
        }
        [data-testid="stMetricLabel"]{color:var(--ti-muted)!important;font-weight:620!important}
        [data-testid="stMetricValue"]{color:var(--ti-navy)!important;font-weight:760!important}
        [data-testid="stDataFrame"],
        [data-testid="stTable"],
        [data-testid="stPlotlyChart"],
        [data-testid="stPyplot"],
        [data-testid="stDeckGlJsonChart"]{
            background:rgba(255,255,255,.96);
            border:1px solid var(--ti-line);
            border-radius:16px;
            padding:8px;
            box-shadow:0 10px 28px rgba(15,31,50,.04);
            overflow:hidden;
        }
        [data-testid="stAlert"]{border-radius:13px;border-width:1px}
        [data-baseweb="select"]>div,
        [data-testid="stTextInput"] input,
        [data-testid="stTextArea"] textarea{
            border-radius:11px!important;
            border-color:#d9e3ec!important;
        }
        .stButton>button,.stDownloadButton>button{
            border-radius:11px;
            font-weight:680;
            min-height:2.65rem;
        }
        [data-testid="stExpander"]{
            background:rgba(255,255,255,.82);
            border:1px solid var(--ti-line);
            border-radius:14px;
        }
        #MainMenu{visibility:hidden}
        footer{visibility:hidden}

        .ti-hero{
            position:relative;
            overflow:hidden;
            background:
                radial-gradient(circle at 92% 28%,rgba(85,214,244,.26),transparent 12rem),
                radial-gradient(circle at 74% 70%,rgba(14,143,176,.18),transparent 17rem),
                linear-gradient(118deg,#071827 0%,#0b2a43 54%,#0b4f68 100%);
            border-radius:24px;
            padding:34px 38px 32px;
            color:white;
            margin-bottom:22px;
            box-shadow:0 18px 50px rgba(7,24,39,.18);
        }
        .ti-hero:after{
            content:"";
            position:absolute;
            width:330px;height:330px;
            border:1px solid rgba(255,255,255,.12);
            border-radius:50%;
            right:-105px;top:-118px;
            box-shadow:0 0 0 38px rgba(255,255,255,.025),0 0 0 82px rgba(255,255,255,.018);
        }
        .ti-badge{
            display:inline-flex;
            padding:6px 10px;
            border-radius:999px;
            background:rgba(85,214,244,.11);
            border:1px solid rgba(85,214,244,.35);
            color:#aeefff;
            font-size:.78rem;
            font-weight:740;
            letter-spacing:.08em;
            text-transform:uppercase;
            margin-bottom:15px;
        }
        .ti-hero h1{color:white!important;font-size:clamp(2.3rem,4vw,3.6rem)!important;margin:0 0 12px!important}
        .ti-hero p{color:#d9edf4;font-size:1.08rem;max-width:880px;margin:0}
        .ti-strip{display:flex;gap:8px;flex-wrap:wrap;margin-top:21px}
        .ti-pill{
            padding:7px 10px;
            background:rgba(255,255,255,.075);
            border:1px solid rgba(255,255,255,.11);
            border-radius:999px;
            color:#effaff;
            font-size:.80rem;
            font-weight:600;
        }
        .ti-kicker{
            color:var(--ti-cyan);
            font-weight:760;
            font-size:.78rem;
            letter-spacing:.10em;
            text-transform:uppercase;
            margin-top:8px;
        }
        .ti-card{
            height:100%;
            background:rgba(255,255,255,.96);
            border:1px solid var(--ti-line);
            border-radius:18px;
            padding:20px;
            box-shadow:0 9px 28px rgba(15,31,50,.05);
        }
        .ti-card-title{font-weight:730;color:var(--ti-navy);margin-bottom:6px}
        .ti-card-copy{color:var(--ti-muted);font-size:.92rem;line-height:1.45}
        .ti-flow{
            background:white;
            border:1px solid var(--ti-line);
            border-radius:18px;
            padding:18px 20px;
            box-shadow:0 9px 28px rgba(15,31,50,.04);
            margin:12px 0 20px;
        }
        .ti-flow-row{display:flex;align-items:center;gap:10px;flex-wrap:wrap}
        .ti-node{
            padding:9px 12px;
            border-radius:11px;
            background:#eef6f8;
            color:#17445a;
            font-weight:680;
            font-size:.84rem;
            border:1px solid #d7e9ef;
        }
        .ti-arrow{color:#78a6b8;font-weight:900}
        </style>
        ''',
        unsafe_allow_html=True,
    )
