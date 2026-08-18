import math
import re
from concurrent.futures import ThreadPoolExecutor, as_completed
from urllib.parse import quote_plus

import feedparser
import numpy as np
import pandas as pd
import streamlit as st
from textblob import TextBlob
from vaderSentiment.vaderSentiment import SentimentIntensityAnalyzer


CONTENT_LANGUAGES = {
    "English": "en",
    "Arabic": "ar",
    "Russian": "ru",
    "French": "fr",
    "Spanish": "es",
    "German": "de",
    "Japanese": "ja",
    "Chinese": "zh",
    "Korean": "ko",
    "Portuguese": "pt",
    "Italian": "it",
    "Turkish": "tr",
    "Hindi": "hi",
    "Dutch": "nl",
}

DEFAULT_CONTENT_LANGUAGES = [
    "English",
    "Arabic",
    "Russian",
    "French",
    "Spanish",
    "German",
    "Japanese",
    "Chinese",
]

NEWS_PROFILES = {
    "en": {
        "label": "English",
        "hl": "en-US",
        "gl": "US",
        "ceid": "US:en",
        "edition": "United States",
    },
    "ar": {
        "label": "Arabic",
        "hl": "ar",
        "gl": "OM",
        "ceid": "OM:ar",
        "edition": "Oman",
    },
    "ru": {
        "label": "Russian",
        "hl": "ru",
        "gl": "RU",
        "ceid": "RU:ru",
        "edition": "Russia",
    },
    "fr": {
        "label": "French",
        "hl": "fr",
        "gl": "FR",
        "ceid": "FR:fr",
        "edition": "France",
    },
    "es": {
        "label": "Spanish",
        "hl": "es",
        "gl": "ES",
        "ceid": "ES:es",
        "edition": "Spain",
    },
    "de": {
        "label": "German",
        "hl": "de",
        "gl": "DE",
        "ceid": "DE:de",
        "edition": "Germany",
    },
    "ja": {
        "label": "Japanese",
        "hl": "ja",
        "gl": "JP",
        "ceid": "JP:ja",
        "edition": "Japan",
    },
    "zh": {
        "label": "Chinese",
        "hl": "zh-CN",
        "gl": "CN",
        "ceid": "CN:zh-Hans",
        "edition": "China",
    },
    "ko": {
        "label": "Korean",
        "hl": "ko",
        "gl": "KR",
        "ceid": "KR:ko",
        "edition": "South Korea",
    },
    "pt": {
        "label": "Portuguese",
        "hl": "pt-BR",
        "gl": "BR",
        "ceid": "BR:pt-419",
        "edition": "Brazil",
    },
    "it": {
        "label": "Italian",
        "hl": "it",
        "gl": "IT",
        "ceid": "IT:it",
        "edition": "Italy",
    },
    "tr": {
        "label": "Turkish",
        "hl": "tr",
        "gl": "TR",
        "ceid": "TR:tr",
        "edition": "Türkiye",
    },
    "hi": {
        "label": "Hindi",
        "hl": "hi",
        "gl": "IN",
        "ceid": "IN:hi",
        "edition": "India",
    },
    "nl": {
        "label": "Dutch",
        "hl": "nl",
        "gl": "NL",
        "ceid": "NL:nl",
        "edition": "Netherlands",
    },
}


# Common local-language names improve recall where publishers rarely use
# the Latin/English spelling of an organisation.
ENTITY_ALIASES = {
    "microsoft": {
        "ar": "مايكروسوفت",
        "ru": "Майкрософт",
        "ja": "マイクロソフト",
        "zh": "微软",
    },
    "google": {
        "ar": "غوغل",
        "ru": "Гугл",
        "ja": "グーグル",
        "zh": "谷歌",
    },
    "alphabet": {
        "ar": "ألفابت",
        "ru": "Alphabet",
        "ja": "アルファベット",
        "zh": "Alphabet 谷歌",
    },
    "apple": {
        "ar": "آبل",
        "ru": "Эппл",
        "ja": "アップル",
        "zh": "苹果公司",
    },
    "meta": {
        "ar": "ميتا",
        "ru": "Мета",
        "ja": "メタ",
        "zh": "Meta",
    },
    "tesla": {
        "ar": "تسلا",
        "ru": "Тесла",
        "ja": "テスラ",
        "zh": "特斯拉",
    },
    "amazon": {
        "ar": "أمازون",
        "ru": "Амазон",
        "ja": "アマゾン",
        "zh": "亚马逊",
    },
    "nvidia": {
        "ar": "إنفيديا",
        "ru": "NVIDIA",
        "ja": "エヌビディア",
        "zh": "英伟达",
    },
    "ibm": {
        "ar": "آي بي إم",
        "ru": "IBM",
        "ja": "IBM",
        "zh": "IBM",
    },
    "pfizer": {
        "ar": "فايزر",
        "ru": "Пфайзер",
        "ja": "ファイザー",
        "zh": "辉瑞",
    },
    "toyota": {
        "ar": "تويوتا",
        "ru": "Тойота",
        "ja": "トヨタ",
        "zh": "丰田",
    },
    "sony": {
        "ar": "سوني",
        "ru": "Сони",
        "ja": "ソニー",
        "zh": "索尼",
    },
    "alibaba": {
        "ar": "علي بابا",
        "ru": "Алибаба",
        "ja": "アリババ",
        "zh": "阿里巴巴",
    },
    "world health organization": {
        "ar": "منظمة الصحة العالمية",
        "ru": "Всемирная организация здравоохранения",
        "fr": "Organisation mondiale de la Santé",
        "es": "Organización Mundial de la Salud",
        "de": "Weltgesundheitsorganisation",
        "zh": "世界卫生组织",
        "ja": "世界保健機関",
    },
    "unicef": {
        "ar": "اليونيسف",
        "ru": "ЮНИСЕФ",
        "zh": "联合国儿童基金会",
        "ja": "ユニセフ",
    },
    "european union": {
        "ar": "الاتحاد الأوروبي",
        "ru": "Европейский союз",
        "fr": "Union européenne",
        "es": "Unión Europea",
        "de": "Europäische Union",
        "zh": "欧盟",
        "ja": "欧州連合",
    },
    "sultan qaboos university": {
        "ar": "جامعة السلطان قابوس",
    },
    "oman government": {
        "ar": "حكومة سلطنة عمان",
    },
    "omantel": {
        "ar": "عمانتل",
    },
    "bank muscat": {
        "ar": "بنك مسقط",
    },
    "oq group": {
        "ar": "مجموعة أوكيو",
    },
    "kazan federal university": {
        "ru": "Казанский федеральный университет",
    },
    "sberbank": {
        "ru": "Сбербанк",
    },
    "gazprom": {
        "ru": "Газпром",
    },
    "rosneft": {
        "ru": "Роснефть",
    },
    "lukoil": {
        "ru": "Лукойл",
    },
    "yandex": {
        "ru": "Яндекс",
    },
    "vtb": {
        "ru": "ВТБ",
    },
    "aeroflot": {
        "ru": "Аэрофлот",
    },
}


LEXICONS = {
    "ar": {
        "positive": [
            "نجاح", "إيجابي", "تحسن", "نمو", "تقدم", "ثقة", "آمن",
            "شفاف", "مسؤول", "ابتكار", "ممتاز", "قوي", "استقرار",
        ],
        "negative": [
            "أزمة", "فشل", "خطر", "مخاطر", "سلبي", "اتهام", "فضيحة",
            "انتهاك", "تضليل", "احتيال", "هجوم", "قلق", "تراجع", "خسارة",
        ],
    },
    "ru": {
        "positive": [
            "успех", "рост", "улучш", "позитив", "довер", "безопас",
            "прозрач", "ответствен", "инновац", "стабил", "сильн",
        ],
        "negative": [
            "кризис", "риск", "скандал", "наруш", "обвин", "мошен",
            "дезинформа", "атака", "потер", "паден", "опас", "негатив",
        ],
    },
    "fr": {
        "positive": [
            "succès", "croissance", "amélioration", "positif", "confiance",
            "sécurité", "transparent", "responsable", "innovation", "stable",
        ],
        "negative": [
            "crise", "risque", "scandale", "violation", "accusation",
            "fraude", "désinformation", "attaque", "perte", "baisse", "négatif",
        ],
    },
    "es": {
        "positive": [
            "éxito", "crecimiento", "mejora", "positivo", "confianza",
            "seguridad", "transparente", "responsable", "innovación", "estable",
        ],
        "negative": [
            "crisis", "riesgo", "escándalo", "violación", "acusación",
            "fraude", "desinformación", "ataque", "pérdida", "caída", "negativo",
        ],
    },
    "de": {
        "positive": [
            "erfolg", "wachstum", "verbesser", "positiv", "vertrauen",
            "sicher", "transparent", "verantwort", "innovation", "stabil",
        ],
        "negative": [
            "krise", "risiko", "skandal", "verstoß", "vorwurf",
            "betrug", "desinformation", "angriff", "verlust", "rückgang", "negativ",
        ],
    },
    "ja": {
        "positive": ["成功", "成長", "改善", "信頼", "安全", "透明", "責任", "革新", "安定", "好調"],
        "negative": ["危機", "リスク", "不正", "違反", "疑惑", "詐欺", "偽情報", "攻撃", "損失", "低下", "懸念"],
    },
    "zh": {
        "positive": ["成功", "增长", "改善", "信任", "安全", "透明", "负责", "创新", "稳定", "积极"],
        "negative": ["危机", "风险", "丑闻", "违规", "指控", "欺诈", "虚假信息", "攻击", "损失", "下降", "担忧"],
    },
    "ko": {
        "positive": ["성공", "성장", "개선", "신뢰", "안전", "투명", "책임", "혁신", "안정", "긍정"],
        "negative": ["위기", "위험", "스캔들", "위반", "의혹", "사기", "허위정보", "공격", "손실", "하락", "우려"],
    },
    "pt": {
        "positive": [
            "sucesso", "crescimento", "melhoria", "positivo", "confiança",
            "segurança", "transparente", "responsável", "inovação", "estável",
        ],
        "negative": [
            "crise", "risco", "escândalo", "violação", "acusação",
            "fraude", "desinformação", "ataque", "perda", "queda", "negativo",
        ],
    },
    "it": {
        "positive": [
            "successo", "crescita", "miglioramento", "positivo", "fiducia",
            "sicurezza", "trasparente", "responsabile", "innovazione", "stabile",
        ],
        "negative": [
            "crisi", "rischio", "scandalo", "violazione", "accusa",
            "frode", "disinformazione", "attacco", "perdita", "calo", "negativo",
        ],
    },
    "tr": {
        "positive": [
            "başarı", "büyüme", "iyileş", "olumlu", "güven", "güvenli",
            "şeffaf", "sorumlu", "yenilik", "istikrar",
        ],
        "negative": [
            "kriz", "risk", "skandal", "ihlal", "suçlama", "dolandır",
            "dezenformasyon", "saldırı", "kayıp", "düşüş", "olumsuz",
        ],
    },
    "hi": {
        "positive": ["सफल", "वृद्धि", "सुधार", "सकारात्मक", "विश्वास", "सुरक्षित", "पारदर्शी", "जिम्मेदार", "नवाचार", "स्थिर"],
        "negative": ["संकट", "जोखिम", "घोटाला", "उल्लंघन", "आरोप", "धोखाधड़ी", "दुष्प्रचार", "हमला", "नुकसान", "गिरावट", "चिंता"],
    },
    "nl": {
        "positive": [
            "succes", "groei", "verbeter", "positief", "vertrouwen",
            "veilig", "transparant", "verantwoord", "innovatie", "stabiel",
        ],
        "negative": [
            "crisis", "risico", "schandaal", "overtreding", "beschuldiging",
            "fraude", "desinformatie", "aanval", "verlies", "daling", "negatief",
        ],
    },
}

_vader = SentimentIntensityAnalyzer()


def content_language_selector():
    selected_names = st.sidebar.multiselect(
        "🌍 Data languages | لغات البيانات",
        list(CONTENT_LANGUAGES.keys()),
        default=DEFAULT_CONTENT_LANGUAGES,
        key="trustintel_content_language_names",
        help=(
            "These are the languages TrustIntel AI will collect from public "
            "news editions. Interface language is controlled separately."
        ),
    )

    if not selected_names:
        selected_names = ["English"]

    codes = [
        CONTENT_LANGUAGES[name]
        for name in selected_names
        if name in CONTENT_LANGUAGES
    ]

    st.session_state["trustintel_content_languages"] = codes
    return codes


def get_selected_content_languages():
    return st.session_state.get(
        "trustintel_content_languages",
        [
            CONTENT_LANGUAGES[name]
            for name in DEFAULT_CONTENT_LANGUAGES
        ],
    )


def resolve_query_alias(query, language_code):
    query_text = str(query or "").strip()
    lower = query_text.lower()

    for key, aliases in ENTITY_ALIASES.items():
        if key in lower:
            alias = aliases.get(language_code)
            if alias:
                return alias

    return query_text


def detect_script_language(text, fallback):
    text = str(text or "")

    if re.search(r"[\u0600-\u06FF]", text):
        return "ar"
    if re.search(r"[\u0400-\u04FF]", text):
        return "ru"
    if re.search(r"[\u3040-\u30FF]", text):
        return "ja"
    if re.search(r"[\uAC00-\uD7AF]", text):
        return "ko"
    if re.search(r"[\u4E00-\u9FFF]", text):
        return "zh"
    if re.search(r"[\u0900-\u097F]", text):
        return "hi"

    return fallback


def score_multilingual_sentiment(text, language_code):
    clean = str(text or "").strip()

    if not clean:
        return 0.0, "No text", "Low"

    if language_code == "en":
        return (
            float(_vader.polarity_scores(clean)["compound"]),
            "VADER English",
            "Medium",
        )

    lexicon = LEXICONS.get(language_code)

    if not lexicon:
        return 0.0, "No validated model connected", "Low"

    lower = clean.lower()

    positive_hits = sum(
        1
        for term in lexicon["positive"]
        if term.lower() in lower
    )

    negative_hits = sum(
        1
        for term in lexicon["negative"]
        if term.lower() in lower
    )

    total_hits = positive_hits + negative_hits

    if total_hits == 0:
        return (
            0.0,
            f"Prototype {language_code} lexicon; no polarity terms matched",
            "Low",
        )

    raw = (
        positive_hits - negative_hits
    ) / max(total_hits, 1)

    score = max(-1.0, min(1.0, raw))

    confidence = (
        "Medium"
        if total_hits >= 2
        else "Low"
    )

    return (
        float(score),
        f"Prototype {language_code} lexicon",
        confidence,
    )


def sentiment_label(score):
    score = float(score or 0)

    if score >= 0.3:
        return "Positive"
    if score <= -0.3:
        return "Negative"
    return "Neutral"


def subjectivity_score(text, language_code):
    if language_code != "en":
        return np.nan, "Not validated for this language"

    blob = TextBlob(str(text or ""))
    return (
        float(blob.sentiment.subjectivity),
        "TextBlob English",
    )


def _fetch_one_edition(query, language_code, limit):
    profile = NEWS_PROFILES[language_code]
    search_query = resolve_query_alias(
        query,
        language_code,
    )

    url = (
        "https://news.google.com/rss/search"
        f"?q={quote_plus(search_query)}"
        f"&hl={profile['hl']}"
        f"&gl={profile['gl']}"
        f"&ceid={profile['ceid']}"
    )

    feed = feedparser.parse(url)
    rows = []

    for entry in feed.entries[:limit]:
        headline = getattr(entry, "title", "")
        detected_language = detect_script_language(
            headline,
            language_code,
        )

        sentiment, method, confidence = (
            score_multilingual_sentiment(
                headline,
                detected_language,
            )
        )

        subjectivity, subjectivity_method = (
            subjectivity_score(
                headline,
                detected_language,
            )
        )

        source_obj = getattr(
            entry,
            "source",
            None,
        )

        source = getattr(
            source_obj,
            "title",
            "",
        ) if source_obj else ""

        rows.append(
            {
                "Headline": headline,
                "Link": getattr(entry, "link", ""),
                "Published": getattr(
                    entry,
                    "published",
                    "",
                ),
                "Source": source,
                "Language": NEWS_PROFILES[
                    detected_language
                ]["label"]
                if detected_language
                in NEWS_PROFILES
                else detected_language,
                "Language Code": detected_language,
                "Edition Language": profile["label"],
                "Edition Country": profile["edition"],
                "Query Used": search_query,
                "Sentiment": round(
                    sentiment,
                    3,
                ),
                "Sentiment Label": sentiment_label(
                    sentiment
                ),
                "Sentiment Method": method,
                "Sentiment Confidence": confidence,
                "Subjectivity": (
                    round(
                        float(subjectivity),
                        3,
                    )
                    if pd.notna(subjectivity)
                    else np.nan
                ),
                "Subjectivity Method":
                subjectivity_method,
            }
        )

    return rows


def fetch_multilingual_news(
    query,
    languages=None,
    limit_per_language=8,
):
    query = str(query or "").strip()

    if not query or query.lower() == "nan":
        return pd.DataFrame(
            columns=[
                "Headline",
                "Link",
                "Published",
                "Source",
                "Language",
                "Language Code",
                "Edition Language",
                "Edition Country",
                "Query Used",
                "Sentiment",
                "Sentiment Label",
                "Sentiment Method",
                "Sentiment Confidence",
                "Subjectivity",
                "Subjectivity Method",
            ]
        )

    languages = list(
        languages
        or get_selected_content_languages()
    )

    languages = [
        code
        for code in languages
        if code in NEWS_PROFILES
    ]

    if not languages:
        languages = ["en"]

    rows = []

    with ThreadPoolExecutor(
        max_workers=min(
            8,
            len(languages),
        )
    ) as executor:
        futures = {
            executor.submit(
                _fetch_one_edition,
                query,
                code,
                int(limit_per_language),
            ): code
            for code in languages
        }

        for future in as_completed(futures):
            try:
                rows.extend(
                    future.result()
                )
            except Exception:
                continue

    if not rows:
        return pd.DataFrame()

    df = pd.DataFrame(rows)

    df["_dedupe"] = (
        df["Headline"]
        .fillna("")
        .astype(str)
        .str.lower()
        .str.replace(
            r"\s+",
            " ",
            regex=True,
        )
        .str.strip()
    )

    df = (
        df.drop_duplicates(
            subset=["_dedupe"],
            keep="first",
        )
        .drop(
            columns=["_dedupe"]
        )
        .reset_index(drop=True)
    )

    return df


def language_coverage(news_df):
    if news_df is None or news_df.empty:
        return pd.DataFrame(
            columns=[
                "Language",
                "Narratives",
                "Average Sentiment",
                "Negative Share %",
            ]
        )

    grouped = news_df.groupby(
        "Language",
        dropna=False,
    )

    summary = grouped.agg(
        Narratives=(
            "Headline",
            "count",
        ),
        Average_Sentiment=(
            "Sentiment",
            "mean",
        ),
    ).reset_index()

    negative_share = grouped[
        "Sentiment"
    ].apply(
        lambda values:
        float(
            values.le(-0.3).mean()
            * 100
        )
    )

    summary[
        "Negative Share %"
    ] = summary[
        "Language"
    ].map(
        negative_share
    )

    summary[
        "Average Sentiment"
    ] = summary[
        "Average_Sentiment"
    ].round(3)

    summary = summary.drop(
        columns=[
            "Average_Sentiment"
        ]
    )

    return summary.sort_values(
        "Narratives",
        ascending=False,
    ).reset_index(drop=True)


def safe_sentiment_stats(news_df):
    if news_df is None or news_df.empty:
        return {
            "count": 0,
            "mean": 0.0,
            "abs_mean": 0.0,
            "std": 0.0,
            "negative_ratio": 0.0,
            "positive_ratio": 0.0,
        }

    scores = (
        news_df["Sentiment"]
        .fillna(0)
        .astype(float)
    )

    return {
        "count": int(len(scores)),
        "mean": float(scores.mean()),
        "abs_mean": float(scores.abs().mean()),
        "std": float(scores.std(ddof=0)),
        "negative_ratio": float(
            scores.le(-0.3).mean()
        ),
        "positive_ratio": float(
            scores.ge(0.3).mean()
        ),
    }
