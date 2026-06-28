import re
from urllib.parse import quote_plus

import feedparser
import requests
from textblob import TextBlob
from vaderSentiment.vaderSentiment import SentimentIntensityAnalyzer


CATEGORY_KEYWORDS = {
    "Responsible AI and governance": [
        "responsible ai",
        "ai governance",
        "trustworthy ai",
        "ai ethics",
        "ethical ai",
        "ai policy",
    ],
    "Transparency and accountability": [
        "ai transparency",
        "algorithmic transparency",
        "algorithmic accountability",
        "explainable ai",
        "ai disclosure",
        "model transparency",
    ],
    "Privacy and data governance": [
        "ai privacy",
        "data privacy",
        "data governance",
        "data protection",
        "personal data",
        "gdpr",
    ],
    "Fairness, bias and inclusion": [
        "ai bias",
        "algorithmic bias",
        "algorithmic fairness",
        "discrimination",
        "inclusive ai",
        "fairness",
    ],
    "Human oversight and safety": [
        "human oversight",
        "ai safety",
        "automation risk",
        "algorithmic decision",
        "ai risk",
        "ai regulation",
    ],
    "Sustainability and infrastructure": [
        "sustainable ai",
        "ai sustainability",
        "green ai",
        "data center energy",
        "data centre energy",
        "carbon emissions",
    ],
    "Misinformation and stakeholder trust": [
        "ai misinformation",
        "deepfake",
        "synthetic media",
        "disinformation",
        "stakeholder trust",
        "public trust",
    ],
}

LANGUAGE_PROFILES = {
    "en": {
        "label": "English",
        "hl": "en-US",
        "gl": "US",
        "ceid": "US:en",
        "sentiment_method": "English lexical sentiment prototype",
    },
    "ar": {
        "label": "Arabic",
        "hl": "ar",
        "gl": "AE",
        "ceid": "AE:ar",
        "sentiment_method": "Keyword-only prototype; Arabic sentiment validation required",
    },
    "ru": {
        "label": "Russian",
        "hl": "ru",
        "gl": "RU",
        "ceid": "RU:ru",
        "sentiment_method": "Keyword-only prototype; Russian sentiment validation required",
    },
    "fr": {
        "label": "French",
        "hl": "fr",
        "gl": "FR",
        "ceid": "FR:fr",
        "sentiment_method": "Keyword-only prototype; French sentiment validation required",
    },
    "es": {
        "label": "Spanish",
        "hl": "es",
        "gl": "ES",
        "ceid": "ES:es",
        "sentiment_method": "Keyword-only prototype; Spanish sentiment validation required",
    },
    "de": {
        "label": "German",
        "hl": "de",
        "gl": "DE",
        "ceid": "DE:de",
        "sentiment_method": "Keyword-only prototype; German sentiment validation required",
    },
}

LANGUAGE_PROFILES.update({
    "en_us": {
        "label": "English - United States",
        "base_language": "en",
        "hl": "en-US",
        "gl": "US",
        "ceid": "US:en",
        "country": "United States",
        "region": "North America",
        "iso3": "USA",
        "latitude": 37.0902,
        "longitude": -95.7129,
        "sentiment_method": "English VADER/TextBlob prototype",
    },
    "en_gb": {
        "label": "English - United Kingdom",
        "base_language": "en",
        "hl": "en-GB",
        "gl": "GB",
        "ceid": "GB:en",
        "country": "United Kingdom",
        "region": "Europe",
        "iso3": "GBR",
        "latitude": 55.3781,
        "longitude": -3.4360,
        "sentiment_method": "English VADER/TextBlob prototype",
    },
    "ar_om": {
        "label": "Arabic - Oman",
        "base_language": "ar",
        "hl": "ar",
        "gl": "OM",
        "ceid": "OM:ar",
        "country": "Oman",
        "region": "Middle East",
        "iso3": "OMN",
        "latitude": 21.4735,
        "longitude": 55.9754,
        "sentiment_method": "Prototype Arabic lexicon sentiment; validation required",
    },
    "ar_ae": {
        "label": "Arabic - United Arab Emirates",
        "base_language": "ar",
        "hl": "ar",
        "gl": "AE",
        "ceid": "AE:ar",
        "country": "United Arab Emirates",
        "region": "Middle East",
        "iso3": "ARE",
        "latitude": 23.4241,
        "longitude": 53.8478,
        "sentiment_method": "Prototype Arabic lexicon sentiment; validation required",
    },
    "ar_sa": {
        "label": "Arabic - Saudi Arabia",
        "base_language": "ar",
        "hl": "ar",
        "gl": "SA",
        "ceid": "SA:ar",
        "country": "Saudi Arabia",
        "region": "Middle East",
        "iso3": "SAU",
        "latitude": 23.8859,
        "longitude": 45.0792,
        "sentiment_method": "Prototype Arabic lexicon sentiment; validation required",
    },
    "ar_qa": {
        "label": "Arabic - Qatar",
        "base_language": "ar",
        "hl": "ar",
        "gl": "QA",
        "ceid": "QA:ar",
        "country": "Qatar",
        "region": "Middle East",
        "iso3": "QAT",
        "latitude": 25.3548,
        "longitude": 51.1839,
        "sentiment_method": "Prototype Arabic lexicon sentiment; validation required",
    },
    "ru_ru": {
        "label": "Russian - Russia",
        "base_language": "ru",
        "hl": "ru",
        "gl": "RU",
        "ceid": "RU:ru",
        "country": "Russia",
        "region": "Eurasia",
        "iso3": "RUS",
        "latitude": 61.5240,
        "longitude": 105.3188,
        "sentiment_method": "Prototype Russian lexicon sentiment; validation required",
    },
    "fr_fr": {
        "label": "French - France",
        "base_language": "fr",
        "hl": "fr",
        "gl": "FR",
        "ceid": "FR:fr",
        "country": "France",
        "region": "Europe",
        "iso3": "FRA",
        "latitude": 46.2276,
        "longitude": 2.2137,
        "sentiment_method": "Prototype French lexicon sentiment; validation required",
    },
    "es_es": {
        "label": "Spanish - Spain",
        "base_language": "es",
        "hl": "es",
        "gl": "ES",
        "ceid": "ES:es",
        "country": "Spain",
        "region": "Europe",
        "iso3": "ESP",
        "latitude": 40.4637,
        "longitude": -3.7492,
        "sentiment_method": "Prototype Spanish lexicon sentiment; validation required",
    },
    "de_de": {
        "label": "German - Germany",
        "base_language": "de",
        "hl": "de",
        "gl": "DE",
        "ceid": "DE:de",
        "country": "Germany",
        "region": "Europe",
        "iso3": "DEU",
        "latitude": 51.1657,
        "longitude": 10.4515,
        "sentiment_method": "Prototype German lexicon sentiment; validation required",
    },
    "it_it": {
        "label": "Italian - Italy",
        "base_language": "it",
        "hl": "it",
        "gl": "IT",
        "ceid": "IT:it",
        "country": "Italy",
        "region": "Europe",
        "iso3": "ITA",
        "latitude": 41.8719,
        "longitude": 12.5674,
        "sentiment_method": "Prototype Italian lexicon sentiment; validation required",
    },
    "pt_br": {
        "label": "Portuguese - Brazil",
        "base_language": "pt",
        "hl": "pt-BR",
        "gl": "BR",
        "ceid": "BR:pt-419",
        "country": "Brazil",
        "region": "Latin America",
        "iso3": "BRA",
        "latitude": -14.2350,
        "longitude": -51.9253,
        "sentiment_method": "Prototype Portuguese lexicon sentiment; validation required",
    },
    "tr_tr": {
        "label": "Turkish - Turkiye",
        "base_language": "tr",
        "hl": "tr",
        "gl": "TR",
        "ceid": "TR:tr",
        "country": "Turkiye",
        "region": "Europe / Middle East",
        "iso3": "TUR",
        "latitude": 38.9637,
        "longitude": 35.2433,
        "sentiment_method": "Prototype Turkish lexicon sentiment; validation required",
    },
    "hi_in": {
        "label": "Hindi - India",
        "base_language": "hi",
        "hl": "hi",
        "gl": "IN",
        "ceid": "IN:hi",
        "country": "India",
        "region": "South Asia",
        "iso3": "IND",
        "latitude": 20.5937,
        "longitude": 78.9629,
        "sentiment_method": "Prototype Hindi lexicon sentiment; validation required",
    },
    "zh_cn": {
        "label": "Chinese - China",
        "base_language": "zh",
        "hl": "zh-CN",
        "gl": "CN",
        "ceid": "CN:zh-Hans",
        "country": "China",
        "region": "East Asia",
        "iso3": "CHN",
        "latitude": 35.8617,
        "longitude": 104.1954,
        "sentiment_method": "Prototype Chinese lexicon sentiment; validation required",
    },
    "ja_jp": {
        "label": "Japanese - Japan",
        "base_language": "ja",
        "hl": "ja",
        "gl": "JP",
        "ceid": "JP:ja",
        "country": "Japan",
        "region": "East Asia",
        "iso3": "JPN",
        "latitude": 36.2048,
        "longitude": 138.2529,
        "sentiment_method": "Prototype Japanese lexicon sentiment; validation required",
    },
    "ko_kr": {
        "label": "Korean - South Korea",
        "base_language": "ko",
        "hl": "ko",
        "gl": "KR",
        "ceid": "KR:ko",
        "country": "South Korea",
        "region": "East Asia",
        "iso3": "KOR",
        "latitude": 35.9078,
        "longitude": 127.7669,
        "sentiment_method": "Prototype Korean lexicon sentiment; validation required",
    },
    "nl_nl": {
        "label": "Dutch - Netherlands",
        "base_language": "nl",
        "hl": "nl",
        "gl": "NL",
        "ceid": "NL:nl",
        "country": "Netherlands",
        "region": "Europe",
        "iso3": "NLD",
        "latitude": 52.1326,
        "longitude": 5.2913,
        "sentiment_method": "Prototype Dutch lexicon sentiment; validation required",
    },
})

LANGUAGE_PROFILES.update({
    "en_ca": {
        "label": "English - Canada",
        "base_language": "en",
        "hl": "en-CA",
        "gl": "CA",
        "ceid": "CA:en",
        "country": "Canada",
        "region": "North America",
        "iso3": "CAN",
        "latitude": 56.1304,
        "longitude": -106.3468,
        "sentiment_method": "English VADER/TextBlob prototype",
    },
    "en_au": {
        "label": "English - Australia",
        "base_language": "en",
        "hl": "en-AU",
        "gl": "AU",
        "ceid": "AU:en",
        "country": "Australia",
        "region": "Oceania",
        "iso3": "AUS",
        "latitude": -25.2744,
        "longitude": 133.7751,
        "sentiment_method": "English VADER/TextBlob prototype",
    },
    "fr_ca": {
        "label": "French - Canada",
        "base_language": "fr",
        "hl": "fr-CA",
        "gl": "CA",
        "ceid": "CA:fr",
        "country": "Canada",
        "region": "North America",
        "iso3": "CAN",
        "latitude": 56.1304,
        "longitude": -106.3468,
        "sentiment_method": "Prototype French lexicon sentiment; validation required",
    },
    "es_mx": {
        "label": "Spanish - Mexico",
        "base_language": "es",
        "hl": "es-419",
        "gl": "MX",
        "ceid": "MX:es-419",
        "country": "Mexico",
        "region": "Latin America",
        "iso3": "MEX",
        "latitude": 23.6345,
        "longitude": -102.5528,
        "sentiment_method": "Prototype Spanish lexicon sentiment; validation required",
    },
    "es_ar": {
        "label": "Spanish - Argentina",
        "base_language": "es",
        "hl": "es-419",
        "gl": "AR",
        "ceid": "AR:es-419",
        "country": "Argentina",
        "region": "Latin America",
        "iso3": "ARG",
        "latitude": -38.4161,
        "longitude": -63.6167,
        "sentiment_method": "Prototype Spanish lexicon sentiment; validation required",
    },
    "pt_pt": {
        "label": "Portuguese - Portugal",
        "base_language": "pt",
        "hl": "pt-PT",
        "gl": "PT",
        "ceid": "PT:pt-150",
        "country": "Portugal",
        "region": "Europe",
        "iso3": "PRT",
        "latitude": 39.3999,
        "longitude": -8.2245,
        "sentiment_method": "Prototype Portuguese lexicon sentiment; validation required",
    },
    "sv_se": {
        "label": "Swedish - Sweden",
        "base_language": "sv",
        "hl": "sv",
        "gl": "SE",
        "ceid": "SE:sv",
        "country": "Sweden",
        "region": "Europe",
        "iso3": "SWE",
        "latitude": 60.1282,
        "longitude": 18.6435,
        "sentiment_method": "Prototype Swedish lexicon sentiment; validation required",
    },
    "no_no": {
        "label": "Norwegian - Norway",
        "base_language": "no",
        "hl": "no",
        "gl": "NO",
        "ceid": "NO:no",
        "country": "Norway",
        "region": "Europe",
        "iso3": "NOR",
        "latitude": 60.4720,
        "longitude": 8.4689,
        "sentiment_method": "Prototype Norwegian lexicon sentiment; validation required",
    },
    "da_dk": {
        "label": "Danish - Denmark",
        "base_language": "da",
        "hl": "da",
        "gl": "DK",
        "ceid": "DK:da",
        "country": "Denmark",
        "region": "Europe",
        "iso3": "DNK",
        "latitude": 56.2639,
        "longitude": 9.5018,
        "sentiment_method": "Prototype Danish lexicon sentiment; validation required",
    },
    "fi_fi": {
        "label": "Finnish - Finland",
        "base_language": "fi",
        "hl": "fi",
        "gl": "FI",
        "ceid": "FI:fi",
        "country": "Finland",
        "region": "Europe",
        "iso3": "FIN",
        "latitude": 61.9241,
        "longitude": 25.7482,
        "sentiment_method": "Prototype Finnish lexicon sentiment; validation required",
    },
    "pl_pl": {
        "label": "Polish - Poland",
        "base_language": "pl",
        "hl": "pl",
        "gl": "PL",
        "ceid": "PL:pl",
        "country": "Poland",
        "region": "Europe",
        "iso3": "POL",
        "latitude": 51.9194,
        "longitude": 19.1451,
        "sentiment_method": "Prototype Polish lexicon sentiment; validation required",
    },
    "cs_cz": {
        "label": "Czech - Czechia",
        "base_language": "cs",
        "hl": "cs",
        "gl": "CZ",
        "ceid": "CZ:cs",
        "country": "Czechia",
        "region": "Europe",
        "iso3": "CZE",
        "latitude": 49.8175,
        "longitude": 15.4730,
        "sentiment_method": "Prototype Czech lexicon sentiment; validation required",
    },
    "hu_hu": {
        "label": "Hungarian - Hungary",
        "base_language": "hu",
        "hl": "hu",
        "gl": "HU",
        "ceid": "HU:hu",
        "country": "Hungary",
        "region": "Europe",
        "iso3": "HUN",
        "latitude": 47.1625,
        "longitude": 19.5033,
        "sentiment_method": "Prototype Hungarian lexicon sentiment; validation required",
    },
    "ro_ro": {
        "label": "Romanian - Romania",
        "base_language": "ro",
        "hl": "ro",
        "gl": "RO",
        "ceid": "RO:ro",
        "country": "Romania",
        "region": "Europe",
        "iso3": "ROU",
        "latitude": 45.9432,
        "longitude": 24.9668,
        "sentiment_method": "Prototype Romanian lexicon sentiment; validation required",
    },
    "uk_ua": {
        "label": "Ukrainian - Ukraine",
        "base_language": "uk",
        "hl": "uk",
        "gl": "UA",
        "ceid": "UA:uk",
        "country": "Ukraine",
        "region": "Europe",
        "iso3": "UKR",
        "latitude": 48.3794,
        "longitude": 31.1656,
        "sentiment_method": "Prototype Ukrainian lexicon sentiment; validation required",
    },
    "el_gr": {
        "label": "Greek - Greece",
        "base_language": "el",
        "hl": "el",
        "gl": "GR",
        "ceid": "GR:el",
        "country": "Greece",
        "region": "Europe",
        "iso3": "GRC",
        "latitude": 39.0742,
        "longitude": 21.8243,
        "sentiment_method": "Prototype Greek lexicon sentiment; validation required",
    },
    "he_il": {
        "label": "Hebrew - Israel",
        "base_language": "he",
        "hl": "iw",
        "gl": "IL",
        "ceid": "IL:iw",
        "country": "Israel",
        "region": "Middle East",
        "iso3": "ISR",
        "latitude": 31.0461,
        "longitude": 34.8516,
        "sentiment_method": "Prototype Hebrew lexicon sentiment; validation required",
    },
    "fa_ir": {
        "label": "Persian - Iran",
        "base_language": "fa",
        "hl": "fa",
        "gl": "IR",
        "ceid": "IR:fa",
        "country": "Iran",
        "region": "Middle East",
        "iso3": "IRN",
        "latitude": 32.4279,
        "longitude": 53.6880,
        "sentiment_method": "Prototype Persian lexicon sentiment; validation required",
    },
    "ur_pk": {
        "label": "Urdu - Pakistan",
        "base_language": "ur",
        "hl": "ur",
        "gl": "PK",
        "ceid": "PK:ur",
        "country": "Pakistan",
        "region": "South Asia",
        "iso3": "PAK",
        "latitude": 30.3753,
        "longitude": 69.3451,
        "sentiment_method": "Prototype Urdu lexicon sentiment; validation required",
    },
    "id_id": {
        "label": "Indonesian - Indonesia",
        "base_language": "id",
        "hl": "id",
        "gl": "ID",
        "ceid": "ID:id",
        "country": "Indonesia",
        "region": "Southeast Asia",
        "iso3": "IDN",
        "latitude": -0.7893,
        "longitude": 113.9213,
        "sentiment_method": "Prototype Indonesian lexicon sentiment; validation required",
    },
    "ms_my": {
        "label": "Malay - Malaysia",
        "base_language": "ms",
        "hl": "ms",
        "gl": "MY",
        "ceid": "MY:ms",
        "country": "Malaysia",
        "region": "Southeast Asia",
        "iso3": "MYS",
        "latitude": 4.2105,
        "longitude": 101.9758,
        "sentiment_method": "Prototype Malay lexicon sentiment; validation required",
    },
    "th_th": {
        "label": "Thai - Thailand",
        "base_language": "th",
        "hl": "th",
        "gl": "TH",
        "ceid": "TH:th",
        "country": "Thailand",
        "region": "Southeast Asia",
        "iso3": "THA",
        "latitude": 15.8700,
        "longitude": 100.9925,
        "sentiment_method": "Prototype Thai lexicon sentiment; validation required",
    },
    "vi_vn": {
        "label": "Vietnamese - Vietnam",
        "base_language": "vi",
        "hl": "vi",
        "gl": "VN",
        "ceid": "VN:vi",
        "country": "Vietnam",
        "region": "Southeast Asia",
        "iso3": "VNM",
        "latitude": 14.0583,
        "longitude": 108.2772,
        "sentiment_method": "Prototype Vietnamese lexicon sentiment; validation required",
    },
})

LANGUAGE_PROFILES["en"].update({
    "base_language": "en",
    "country": "United States",
    "region": "North America",
    "iso3": "USA",
    "latitude": 37.0902,
    "longitude": -95.7129,
    "sentiment_method": "English VADER/TextBlob prototype",
})
LANGUAGE_PROFILES["ar"].update({
    "base_language": "ar",
    "country": "United Arab Emirates",
    "region": "Middle East",
    "iso3": "ARE",
    "latitude": 23.4241,
    "longitude": 53.8478,
    "sentiment_method": "Prototype Arabic lexicon sentiment; validation required",
})
LANGUAGE_PROFILES["ru"].update({
    "base_language": "ru",
    "country": "Russia",
    "region": "Eurasia",
    "iso3": "RUS",
    "latitude": 61.5240,
    "longitude": 105.3188,
    "sentiment_method": "Prototype Russian lexicon sentiment; validation required",
})
LANGUAGE_PROFILES["fr"].update({
    "base_language": "fr",
    "country": "France",
    "region": "Europe",
    "iso3": "FRA",
    "latitude": 46.2276,
    "longitude": 2.2137,
    "sentiment_method": "Prototype French lexicon sentiment; validation required",
})
LANGUAGE_PROFILES["es"].update({
    "base_language": "es",
    "country": "Spain",
    "region": "Europe",
    "iso3": "ESP",
    "latitude": 40.4637,
    "longitude": -3.7492,
    "sentiment_method": "Prototype Spanish lexicon sentiment; validation required",
})
LANGUAGE_PROFILES["de"].update({
    "base_language": "de",
    "country": "Germany",
    "region": "Europe",
    "iso3": "DEU",
    "latitude": 51.1657,
    "longitude": 10.4515,
    "sentiment_method": "Prototype German lexicon sentiment; validation required",
})

LOCALIZED_CATEGORY_KEYWORDS = {
    "ar": {
        "Responsible AI and governance": [
            "الذكاء الاصطناعي المسؤول",
            "حوكمة الذكاء الاصطناعي",
            "أخلاقيات الذكاء الاصطناعي",
        ],
        "Transparency and accountability": [
            "شفافية الذكاء الاصطناعي",
            "المساءلة الخوارزمية",
            "قابلية تفسير الذكاء الاصطناعي",
        ],
        "Privacy and data governance": [
            "خصوصية البيانات",
            "حوكمة البيانات",
            "حماية البيانات",
        ],
        "Fairness, bias and inclusion": [
            "تحيز الذكاء الاصطناعي",
            "العدالة الخوارزمية",
            "التمييز",
        ],
        "Human oversight and safety": [
            "الإشراف البشري",
            "سلامة الذكاء الاصطناعي",
            "مخاطر الذكاء الاصطناعي",
        ],
        "Sustainability and infrastructure": [
            "استدامة الذكاء الاصطناعي",
            "مراكز البيانات",
            "انبعاثات الكربون",
        ],
        "Misinformation and stakeholder trust": [
            "المعلومات المضللة",
            "التزييف العميق",
            "ثقة الجمهور",
        ],
    },
    "ru": {
        "Responsible AI and governance": [
            "ответственный искусственный интеллект",
            "управление искусственным интеллектом",
            "этика искусственного интеллекта",
        ],
        "Transparency and accountability": [
            "прозрачность искусственного интеллекта",
            "алгоритмическая подотчетность",
            "объяснимый искусственный интеллект",
        ],
        "Privacy and data governance": [
            "конфиденциальность данных",
            "управление данными",
            "защита данных",
        ],
        "Fairness, bias and inclusion": [
            "предвзятость искусственного интеллекта",
            "алгоритмическая справедливость",
            "дискриминация",
        ],
        "Human oversight and safety": [
            "человеческий контроль",
            "безопасность искусственного интеллекта",
            "риски искусственного интеллекта",
        ],
        "Sustainability and infrastructure": [
            "устойчивый искусственный интеллект",
            "энергопотребление дата-центров",
            "углеродные выбросы",
        ],
        "Misinformation and stakeholder trust": [
            "дезинформация",
            "дипфейк",
            "общественное доверие",
        ],
    },
    "fr": {
        "Responsible AI and governance": [
            "intelligence artificielle responsable",
            "gouvernance de l'intelligence artificielle",
            "ethique de l'intelligence artificielle",
        ],
        "Transparency and accountability": [
            "transparence algorithmique",
            "responsabilite algorithmique",
            "ia explicable",
        ],
        "Privacy and data governance": [
            "confidentialite des donnees",
            "gouvernance des donnees",
            "protection des donnees",
        ],
        "Fairness, bias and inclusion": [
            "biais algorithmique",
            "equite algorithmique",
            "discrimination",
        ],
        "Human oversight and safety": [
            "supervision humaine",
            "securite de l'intelligence artificielle",
            "risque de l'intelligence artificielle",
        ],
        "Sustainability and infrastructure": [
            "intelligence artificielle durable",
            "energie des centres de donnees",
            "emissions carbone",
        ],
        "Misinformation and stakeholder trust": [
            "desinformation",
            "hypertrucage",
            "confiance du public",
        ],
    },
    "es": {
        "Responsible AI and governance": [
            "inteligencia artificial responsable",
            "gobernanza de la inteligencia artificial",
            "etica de la inteligencia artificial",
        ],
        "Transparency and accountability": [
            "transparencia algoritmica",
            "responsabilidad algoritmica",
            "ia explicable",
        ],
        "Privacy and data governance": [
            "privacidad de datos",
            "gobernanza de datos",
            "proteccion de datos",
        ],
        "Fairness, bias and inclusion": [
            "sesgo algoritmico",
            "equidad algoritmica",
            "discriminacion",
        ],
        "Human oversight and safety": [
            "supervision humana",
            "seguridad de la inteligencia artificial",
            "riesgo de inteligencia artificial",
        ],
        "Sustainability and infrastructure": [
            "inteligencia artificial sostenible",
            "energia de centros de datos",
            "emisiones de carbono",
        ],
        "Misinformation and stakeholder trust": [
            "desinformacion",
            "deepfake",
            "confianza publica",
        ],
    },
    "de": {
        "Responsible AI and governance": [
            "verantwortungsvolle ki",
            "ki-governance",
            "ki-ethik",
        ],
        "Transparency and accountability": [
            "algorithmische transparenz",
            "algorithmische rechenschaftspflicht",
            "erklarbare ki",
        ],
        "Privacy and data governance": [
            "datenschutz",
            "daten-governance",
            "schutz personenbezogener daten",
        ],
        "Fairness, bias and inclusion": [
            "algorithmische verzerrung",
            "algorithmische fairness",
            "diskriminierung",
        ],
        "Human oversight and safety": [
            "menschliche aufsicht",
            "ki-sicherheit",
            "ki-risiko",
        ],
        "Sustainability and infrastructure": [
            "nachhaltige ki",
            "energieverbrauch von rechenzentren",
            "kohlenstoffemissionen",
        ],
        "Misinformation and stakeholder trust": [
            "desinformation",
            "deepfake",
            "offentliches vertrauen",
        ],
    },
}

LOCALIZED_CATEGORY_KEYWORDS.update({
    "ar": {
        "Responsible AI and governance": [
            "\u0627\u0644\u0630\u0643\u0627\u0621 \u0627\u0644\u0627\u0635\u0637\u0646\u0627\u0639\u064a \u0627\u0644\u0645\u0633\u0624\u0648\u0644",
            "\u062d\u0648\u0643\u0645\u0629 \u0627\u0644\u0630\u0643\u0627\u0621 \u0627\u0644\u0627\u0635\u0637\u0646\u0627\u0639\u064a",
            "\u0623\u062e\u0644\u0627\u0642\u064a\u0627\u062a \u0627\u0644\u0630\u0643\u0627\u0621 \u0627\u0644\u0627\u0635\u0637\u0646\u0627\u0639\u064a",
        ],
        "Transparency and accountability": [
            "\u0634\u0641\u0627\u0641\u064a\u0629 \u0627\u0644\u0630\u0643\u0627\u0621 \u0627\u0644\u0627\u0635\u0637\u0646\u0627\u0639\u064a",
            "\u0627\u0644\u0645\u0633\u0627\u0621\u0644\u0629 \u0627\u0644\u062e\u0648\u0627\u0631\u0632\u0645\u064a\u0629",
            "\u0642\u0627\u0628\u0644\u064a\u0629 \u062a\u0641\u0633\u064a\u0631 \u0627\u0644\u0630\u0643\u0627\u0621 \u0627\u0644\u0627\u0635\u0637\u0646\u0627\u0639\u064a",
        ],
        "Privacy and data governance": [
            "\u062e\u0635\u0648\u0635\u064a\u0629 \u0627\u0644\u0628\u064a\u0627\u0646\u0627\u062a",
            "\u062d\u0648\u0643\u0645\u0629 \u0627\u0644\u0628\u064a\u0627\u0646\u0627\u062a",
            "\u062d\u0645\u0627\u064a\u0629 \u0627\u0644\u0628\u064a\u0627\u0646\u0627\u062a",
        ],
        "Fairness, bias and inclusion": [
            "\u062a\u062d\u064a\u0632 \u0627\u0644\u0630\u0643\u0627\u0621 \u0627\u0644\u0627\u0635\u0637\u0646\u0627\u0639\u064a",
            "\u0627\u0644\u0639\u062f\u0627\u0644\u0629 \u0627\u0644\u062e\u0648\u0627\u0631\u0632\u0645\u064a\u0629",
            "\u0627\u0644\u062a\u0645\u064a\u064a\u0632",
        ],
        "Human oversight and safety": [
            "\u0627\u0644\u0625\u0634\u0631\u0627\u0641 \u0627\u0644\u0628\u0634\u0631\u064a",
            "\u0633\u0644\u0627\u0645\u0629 \u0627\u0644\u0630\u0643\u0627\u0621 \u0627\u0644\u0627\u0635\u0637\u0646\u0627\u0639\u064a",
            "\u0645\u062e\u0627\u0637\u0631 \u0627\u0644\u0630\u0643\u0627\u0621 \u0627\u0644\u0627\u0635\u0637\u0646\u0627\u0639\u064a",
        ],
        "Sustainability and infrastructure": [
            "\u0627\u0633\u062a\u062f\u0627\u0645\u0629 \u0627\u0644\u0630\u0643\u0627\u0621 \u0627\u0644\u0627\u0635\u0637\u0646\u0627\u0639\u064a",
            "\u0645\u0631\u0627\u0643\u0632 \u0627\u0644\u0628\u064a\u0627\u0646\u0627\u062a",
            "\u0627\u0646\u0628\u0639\u0627\u062b\u0627\u062a \u0627\u0644\u0643\u0631\u0628\u0648\u0646",
        ],
        "Misinformation and stakeholder trust": [
            "\u0627\u0644\u0645\u0639\u0644\u0648\u0645\u0627\u062a \u0627\u0644\u0645\u0636\u0644\u0644\u0629",
            "\u0627\u0644\u062a\u0632\u064a\u064a\u0641 \u0627\u0644\u0639\u0645\u064a\u0642",
            "\u062b\u0642\u0629 \u0627\u0644\u062c\u0645\u0647\u0648\u0631",
        ],
    },
    "it": {
        "Responsible AI and governance": ["intelligenza artificiale responsabile", "governance dell'intelligenza artificiale", "etica dell'intelligenza artificiale"],
        "Transparency and accountability": ["trasparenza algoritmica", "responsabilita algoritmica", "ia spiegabile"],
        "Privacy and data governance": ["privacy dei dati", "governance dei dati", "protezione dei dati"],
        "Fairness, bias and inclusion": ["pregiudizio algoritmico", "equita algoritmica", "discriminazione"],
        "Human oversight and safety": ["supervisione umana", "sicurezza dell'intelligenza artificiale", "rischio dell'intelligenza artificiale"],
        "Sustainability and infrastructure": ["intelligenza artificiale sostenibile", "energia dei data center", "emissioni di carbonio"],
        "Misinformation and stakeholder trust": ["disinformazione", "deepfake", "fiducia pubblica"],
    },
    "pt": {
        "Responsible AI and governance": ["inteligencia artificial responsavel", "governanca da inteligencia artificial", "etica da inteligencia artificial"],
        "Transparency and accountability": ["transparencia algoritmica", "responsabilidade algoritmica", "ia explicavel"],
        "Privacy and data governance": ["privacidade de dados", "governanca de dados", "protecao de dados"],
        "Fairness, bias and inclusion": ["vies algoritmico", "equidade algoritmica", "discriminacao"],
        "Human oversight and safety": ["supervisao humana", "seguranca da inteligencia artificial", "risco de inteligencia artificial"],
        "Sustainability and infrastructure": ["inteligencia artificial sustentavel", "energia de data centers", "emissoes de carbono"],
        "Misinformation and stakeholder trust": ["desinformacao", "deepfake", "confianca publica"],
    },
    "tr": {
        "Responsible AI and governance": ["sorumlu yapay zeka", "yapay zeka yonetisimi", "yapay zeka etigi"],
        "Transparency and accountability": ["algoritmik seffaflik", "algoritmik hesap verebilirlik", "aciklanabilir yapay zeka"],
        "Privacy and data governance": ["veri gizliligi", "veri yonetisimi", "veri koruma"],
        "Fairness, bias and inclusion": ["algoritmik onyargi", "algoritmik adalet", "ayrimcilik"],
        "Human oversight and safety": ["insan gozetimi", "yapay zeka guvenligi", "yapay zeka riski"],
        "Sustainability and infrastructure": ["surdurulebilir yapay zeka", "veri merkezi enerjisi", "karbon emisyonlari"],
        "Misinformation and stakeholder trust": ["dezenformasyon", "deepfake", "kamu guveni"],
    },
    "nl": {
        "Responsible AI and governance": ["verantwoorde ai", "ai-governance", "ethische ai"],
        "Transparency and accountability": ["algoritmische transparantie", "algoritmische verantwoording", "uitlegbare ai"],
        "Privacy and data governance": ["gegevensprivacy", "datagovernance", "gegevensbescherming"],
        "Fairness, bias and inclusion": ["algoritmische bias", "algoritmische eerlijkheid", "discriminatie"],
        "Human oversight and safety": ["menselijk toezicht", "ai-veiligheid", "ai-risico"],
        "Sustainability and infrastructure": ["duurzame ai", "energie van datacenters", "koolstofemissies"],
        "Misinformation and stakeholder trust": ["desinformatie", "deepfake", "publiek vertrouwen"],
    },
    "zh": {
        "Responsible AI and governance": ["\u8d1f\u8d23\u4efb\u7684\u4eba\u5de5\u667a\u80fd", "\u4eba\u5de5\u667a\u80fd\u6cbb\u7406", "\u4eba\u5de5\u667a\u80fd\u4f26\u7406"],
        "Transparency and accountability": ["\u7b97\u6cd5\u900f\u660e", "\u7b97\u6cd5\u95ee\u8d23", "\u53ef\u89e3\u91ca\u4eba\u5de5\u667a\u80fd"],
        "Privacy and data governance": ["\u6570\u636e\u9690\u79c1", "\u6570\u636e\u6cbb\u7406", "\u6570\u636e\u4fdd\u62a4"],
        "Fairness, bias and inclusion": ["\u7b97\u6cd5\u504f\u89c1", "\u7b97\u6cd5\u516c\u5e73", "\u6b67\u89c6"],
        "Human oversight and safety": ["\u4eba\u7c7b\u76d1\u7763", "\u4eba\u5de5\u667a\u80fd\u5b89\u5168", "\u4eba\u5de5\u667a\u80fd\u98ce\u9669"],
        "Sustainability and infrastructure": ["\u53ef\u6301\u7eed\u4eba\u5de5\u667a\u80fd", "\u6570\u636e\u4e2d\u5fc3\u80fd\u8017", "\u78b3\u6392\u653e"],
        "Misinformation and stakeholder trust": ["\u865a\u5047\u4fe1\u606f", "\u6df1\u5ea6\u4f2a\u9020", "\u516c\u4f17\u4fe1\u4efb"],
    },
    "ja": {
        "Responsible AI and governance": ["\u8cac\u4efb\u3042\u308bai", "ai\u30ac\u30d0\u30ca\u30f3\u30b9", "ai\u502b\u7406"],
        "Transparency and accountability": ["\u30a2\u30eb\u30b4\u30ea\u30ba\u30e0\u306e\u900f\u660e\u6027", "\u30a2\u30eb\u30b4\u30ea\u30ba\u30e0\u306e\u8aac\u660e\u8cac\u4efb", "\u8aac\u660e\u53ef\u80fd\u306aai"],
        "Privacy and data governance": ["\u30c7\u30fc\u30bf\u30d7\u30e9\u30a4\u30d0\u30b7\u30fc", "\u30c7\u30fc\u30bf\u30ac\u30d0\u30ca\u30f3\u30b9", "\u30c7\u30fc\u30bf\u4fdd\u8b77"],
        "Fairness, bias and inclusion": ["\u30a2\u30eb\u30b4\u30ea\u30ba\u30e0\u306e\u504f\u308a", "\u30a2\u30eb\u30b4\u30ea\u30ba\u30e0\u306e\u516c\u5e73\u6027", "\u5dee\u5225"],
        "Human oversight and safety": ["\u4eba\u9593\u306b\u3088\u308b\u76e3\u7763", "ai\u5b89\u5168", "ai\u30ea\u30b9\u30af"],
        "Sustainability and infrastructure": ["\u6301\u7d9a\u53ef\u80fd\u306aai", "\u30c7\u30fc\u30bf\u30bb\u30f3\u30bf\u30fc\u306e\u30a8\u30cd\u30eb\u30ae\u30fc", "\u70ad\u7d20\u6392\u51fa"],
        "Misinformation and stakeholder trust": ["\u507d\u60c5\u5831", "\u30c7\u30a3\u30fc\u30d7\u30d5\u30a7\u30a4\u30af", "\u516c\u5171\u306e\u4fe1\u983c"],
    },
    "ko": {
        "Responsible AI and governance": ["\ucc45\uc784 \uc788\ub294 ai", "ai \uac70\ubc84\ub10c\uc2a4", "ai \uc724\ub9ac"],
        "Transparency and accountability": ["\uc54c\uace0\ub9ac\uc998 \ud22c\uba85\uc131", "\uc54c\uace0\ub9ac\uc998 \ucc45\uc784\uc131", "\uc124\uba85 \uac00\ub2a5\ud55c ai"],
        "Privacy and data governance": ["\ub370\uc774\ud130 \ud504\ub77c\uc774\ubc84\uc2dc", "\ub370\uc774\ud130 \uac70\ubc84\ub10c\uc2a4", "\ub370\uc774\ud130 \ubcf4\ud638"],
        "Fairness, bias and inclusion": ["\uc54c\uace0\ub9ac\uc998 \ud3b8\ud5a5", "\uc54c\uace0\ub9ac\uc998 \uacf5\uc815\uc131", "\ucc28\ubcc4"],
        "Human oversight and safety": ["\uc778\uac04 \uac10\ub3c5", "ai \uc548\uc804", "ai \uc704\ud5d8"],
        "Sustainability and infrastructure": ["\uc9c0\uc18d \uac00\ub2a5\ud55c ai", "\ub370\uc774\ud130\uc13c\ud130 \uc5d0\ub108\uc9c0", "\ud0c4\uc18c \ubc30\ucd9c"],
        "Misinformation and stakeholder trust": ["\ud5c8\uc704 \uc815\ubcf4", "\ub525\ud398\uc774\ud06c", "\uacf5\uc911 \uc2e0\ub8b0"],
    },
    "hi": {
        "Responsible AI and governance": ["\u091c\u093f\u092e\u094d\u092e\u0947\u0926\u093e\u0930 \u090f\u0906\u0908", "\u090f\u0906\u0908 \u0936\u093e\u0938\u0928", "\u090f\u0906\u0908 \u0928\u0948\u0924\u093f\u0915\u0924\u093e"],
        "Transparency and accountability": ["\u090f\u0932\u094d\u0917\u094b\u0930\u093f\u0926\u092e\u093f\u0915 \u092a\u093e\u0930\u0926\u0930\u094d\u0936\u093f\u0924\u093e", "\u090f\u0932\u094d\u0917\u094b\u0930\u093f\u0926\u092e\u093f\u0915 \u091c\u0935\u093e\u092c\u0926\u0947\u0939\u0940", "\u0935\u094d\u092f\u093e\u0916\u094d\u092f\u0947\u092f \u090f\u0906\u0908"],
        "Privacy and data governance": ["\u0921\u0947\u091f\u093e \u0917\u094b\u092a\u0928\u0940\u092f\u0924\u093e", "\u0921\u0947\u091f\u093e \u0936\u093e\u0938\u0928", "\u0921\u0947\u091f\u093e \u0938\u0941\u0930\u0915\u094d\u0937\u093e"],
        "Fairness, bias and inclusion": ["\u090f\u0932\u094d\u0917\u094b\u0930\u093f\u0926\u092e\u093f\u0915 \u092a\u0915\u094d\u0937\u092a\u093e\u0924", "\u090f\u0932\u094d\u0917\u094b\u0930\u093f\u0926\u092e\u093f\u0915 \u0928\u094d\u092f\u093e\u092f", "\u092d\u0947\u0926\u092d\u093e\u0935"],
        "Human oversight and safety": ["\u092e\u093e\u0928\u0935 \u0928\u093f\u0917\u0930\u093e\u0928\u0940", "\u090f\u0906\u0908 \u0938\u0941\u0930\u0915\u094d\u0937\u093e", "\u090f\u0906\u0908 \u091c\u094b\u0916\u093f\u092e"],
        "Sustainability and infrastructure": ["\u0938\u0924\u0924 \u090f\u0906\u0908", "\u0921\u0947\u091f\u093e \u0938\u0947\u0902\u091f\u0930 \u090a\u0930\u094d\u091c\u093e", "\u0915\u093e\u0930\u094d\u092c\u0928 \u0909\u0924\u094d\u0938\u0930\u094d\u091c\u0928"],
        "Misinformation and stakeholder trust": ["\u0917\u0932\u0924 \u0938\u0942\u091a\u0928\u093e", "\u0921\u0940\u092a\u092b\u0947\u0915", "\u0938\u093e\u0930\u094d\u0935\u091c\u0928\u093f\u0915 \u0935\u093f\u0936\u094d\u0935\u093e\u0938"],
    },
})

RISK_TERMS = [
    "risk",
    "concern",
    "controversy",
    "criticism",
    "backlash",
    "investigation",
    "lawsuit",
    "breach",
    "ban",
    "warning",
    "misuse",
    "harm",
    "bias",
    "privacy",
    "surveillance",
    "misinformation",
    "disinformation",
    "deepfake",
]

LOCALIZED_RISK_TERMS = [
    "مخاطر",
    "قلق",
    "انتقاد",
    "تحيز",
    "خصوصية",
    "مراقبة",
    "تضليل",
    "дезинформация",
    "риск",
    "критика",
    "конфиденциальность",
    "наблюдение",
    "предвзятость",
    "desinformation",
    "risque",
    "critique",
    "confidentialite",
    "sesgo",
    "riesgo",
    "privacidad",
    "datenschutz",
    "risiko",
]

POSITIVE_GOVERNANCE_TERMS = [
    "framework",
    "standard",
    "responsible",
    "transparent",
    "accountable",
    "safety",
    "policy",
    "oversight",
    "audit",
    "compliance",
    "governance",
]

SENTIMENT_LEXICONS = {
    "ar": {
        "positive": ["\u0645\u0633\u0624\u0648\u0644", "\u0645\u0648\u062b\u0648\u0642", "\u0622\u0645\u0646", "\u062d\u0645\u0627\u064a\u0629", "\u0627\u0645\u062a\u062b\u0627\u0644", "\u0634\u0641\u0627\u0641\u064a\u0629"],
        "negative": ["\u0645\u062e\u0627\u0637\u0631", "\u0642\u0644\u0642", "\u0627\u0646\u062a\u0642\u0627\u062f", "\u062a\u062d\u064a\u0632", "\u062e\u0635\u0648\u0635\u064a\u0629", "\u0627\u0646\u062a\u0647\u0627\u0643", "\u062a\u0636\u0644\u064a\u0644", "\u0623\u0632\u0645\u0629"],
    },
    "ru": {
        "positive": ["\u043e\u0442\u0432\u0435\u0442\u0441\u0442\u0432\u0435\u043d\u043d", "\u043d\u0430\u0434\u0435\u0436\u043d", "\u0431\u0435\u0437\u043e\u043f\u0430\u0441", "\u043f\u0440\u043e\u0437\u0440\u0430\u0447", "\u0437\u0430\u0449\u0438\u0442", "\u0441\u043e\u043e\u0442\u0432\u0435\u0442\u0441\u0442"],
        "negative": ["\u0440\u0438\u0441\u043a", "\u043a\u0440\u0438\u0442\u0438\u043a", "\u043f\u0440\u0435\u0434\u0432\u0437\u044f\u0442", "\u043d\u0430\u0440\u0443\u0448", "\u0434\u0435\u0437\u0438\u043d\u0444\u043e\u0440\u043c", "\u0443\u0433\u0440\u043e\u0437", "\u0441\u043a\u0430\u043d\u0434\u0430\u043b"],
    },
    "fr": {
        "positive": ["responsable", "fiable", "securise", "transparent", "protection", "conformite"],
        "negative": ["risque", "critique", "biais", "confidentialite", "violation", "desinformation", "controverse"],
    },
    "es": {
        "positive": ["responsable", "confiable", "seguro", "transparente", "proteccion", "cumplimiento"],
        "negative": ["riesgo", "critica", "sesgo", "privacidad", "violacion", "desinformacion", "controversia"],
    },
    "de": {
        "positive": ["verantwort", "zuverlassig", "sicher", "transparent", "schutz", "konform"],
        "negative": ["risiko", "kritik", "verzerrung", "datenschutz", "verletzung", "desinformation", "kontroverse"],
    },
    "it": {
        "positive": ["responsabile", "affidabile", "sicuro", "trasparente", "protezione", "conformita"],
        "negative": ["rischio", "critica", "pregiudizio", "privacy", "violazione", "disinformazione", "controversia"],
    },
    "pt": {
        "positive": ["responsavel", "confiavel", "seguro", "transparente", "protecao", "conformidade"],
        "negative": ["risco", "critica", "vies", "privacidade", "violacao", "desinformacao", "controversia"],
    },
    "tr": {
        "positive": ["sorumlu", "guvenilir", "guvenli", "seffaf", "koruma", "uyum"],
        "negative": ["risk", "elestiri", "onyargi", "gizlilik", "ihlal", "dezenformasyon", "tartisma"],
    },
    "nl": {
        "positive": ["verantwoord", "betrouwbaar", "veilig", "transparant", "bescherming", "naleving"],
        "negative": ["risico", "kritiek", "bias", "privacy", "schending", "desinformatie", "controverse"],
    },
    "zh": {
        "positive": ["\u8d1f\u8d23", "\u53ef\u4fe1", "\u5b89\u5168", "\u900f\u660e", "\u4fdd\u62a4", "\u5408\u89c4"],
        "negative": ["\u98ce\u9669", "\u6279\u8bc4", "\u504f\u89c1", "\u9690\u79c1", "\u6cc4\u9732", "\u865a\u5047", "\u4e89\u8bae"],
    },
    "ja": {
        "positive": ["\u8cac\u4efb", "\u4fe1\u983c", "\u5b89\u5168", "\u900f\u660e", "\u4fdd\u8b77", "\u9075\u5b88"],
        "negative": ["\u30ea\u30b9\u30af", "\u6279\u5224", "\u504f\u898b", "\u30d7\u30e9\u30a4\u30d0\u30b7\u30fc", "\u6f0f\u6d29", "\u507d\u60c5\u5831", "\u61f8\u5ff5"],
    },
    "ko": {
        "positive": ["\ucc45\uc784", "\uc2e0\ub8b0", "\uc548\uc804", "\ud22c\uba85", "\ubcf4\ud638", "\uc900\uc218"],
        "negative": ["\uc704\ud5d8", "\ube44\ud310", "\ud3b8\ud5a5", "\uac1c\uc778\uc815\ubcf4", "\uc720\ucd9c", "\ud5c8\uc704", "\uc6b0\ub824"],
    },
    "hi": {
        "positive": ["\u091c\u093f\u092e\u094d\u092e\u0947\u0926\u093e\u0930", "\u0935\u093f\u0936\u094d\u0935\u0938\u0928\u0940\u092f", "\u0938\u0941\u0930\u0915\u094d\u0937\u093f\u0924", "\u092a\u093e\u0930\u0926\u0930\u094d\u0936\u093f\u0924\u093e", "\u0938\u0941\u0930\u0915\u094d\u0937\u093e"],
        "negative": ["\u091c\u094b\u0916\u093f\u092e", "\u0906\u0932\u094b\u091a\u0928\u093e", "\u092a\u0915\u094d\u0937\u092a\u093e\u0924", "\u0917\u094b\u092a\u0928\u0940\u092f\u0924\u093e", "\u0909\u0932\u094d\u0932\u0902\u0918\u0928", "\u092d\u094d\u0930\u093e\u092e\u0915"],
    },
}

SENTIMENT_LEXICONS.update({
    "sv": {
        "positive": ["ansvar", "tillforlitlig", "saker", "transparent", "skydd", "efterlevnad"],
        "negative": ["risk", "kritik", "partiskhet", "integritet", "intrang", "desinformation", "kontrovers"],
    },
    "no": {
        "positive": ["ansvarlig", "palitelig", "trygg", "transparent", "beskyttelse", "etterlevelse"],
        "negative": ["risiko", "kritikk", "skjevhet", "personvern", "brudd", "desinformasjon", "kontrovers"],
    },
    "da": {
        "positive": ["ansvarlig", "palidelig", "sikker", "transparent", "beskyttelse", "overholdelse"],
        "negative": ["risiko", "kritik", "bias", "privatliv", "brud", "desinformation", "kontrovers"],
    },
    "fi": {
        "positive": ["vastuullinen", "luotettava", "turvallinen", "lapinakyva", "suoja", "noudattaminen"],
        "negative": ["riski", "kritiikki", "vinouma", "yksityisyys", "rikkomus", "disinformaatio", "kiista"],
    },
    "pl": {
        "positive": ["odpowiedzial", "wiarygod", "bezpiecz", "przejrzyst", "ochrona", "zgodnosc"],
        "negative": ["ryzyko", "krytyka", "stronnicz", "prywatnosc", "naruszenie", "dezinformacja", "kontrowersja"],
    },
    "cs": {
        "positive": ["odpovedn", "duveryhod", "bezpec", "transparent", "ochrana", "soulad"],
        "negative": ["riziko", "kritika", "zkresleni", "soukromi", "poruseni", "dezinformace", "kontroverze"],
    },
    "hu": {
        "positive": ["felelos", "megbizhato", "biztonsagos", "atlathato", "vedelem", "megfeleles"],
        "negative": ["kockazat", "kritika", "elfogultsag", "adatvedelem", "serelem", "dezinformacio", "vita"],
    },
    "ro": {
        "positive": ["responsabil", "fiabil", "sigur", "transparent", "protectie", "conformitate"],
        "negative": ["risc", "critica", "partinire", "confidentialitate", "incalcare", "dezinformare", "controversa"],
    },
    "uk": {
        "positive": ["\u0432\u0456\u0434\u043f\u043e\u0432\u0456\u0434\u0430\u043b", "\u043d\u0430\u0434\u0456\u0439\u043d", "\u0431\u0435\u0437\u043f\u0435\u0447", "\u043f\u0440\u043e\u0437\u043e\u0440", "\u0437\u0430\u0445\u0438\u0441\u0442"],
        "negative": ["\u0440\u0438\u0437\u0438\u043a", "\u043a\u0440\u0438\u0442\u0438\u043a", "\u0443\u043f\u0435\u0440\u0435\u0434\u0436", "\u043f\u0440\u0438\u0432\u0430\u0442\u043d", "\u043f\u043e\u0440\u0443\u0448", "\u0434\u0435\u0437\u0456\u043d\u0444\u043e\u0440\u043c", "\u0441\u0443\u043f\u0435\u0440\u0435\u0447"],
    },
    "el": {
        "positive": ["\u03c5\u03c0\u03b5\u03c5\u03b8\u03c5\u03bd", "\u03b1\u03be\u03b9\u03bf\u03c0\u03b9\u03c3\u03c4", "\u03b1\u03c3\u03c6\u03b1\u03bb", "\u03b4\u03b9\u03b1\u03c6\u03b1\u03bd", "\u03c0\u03c1\u03bf\u03c3\u03c4\u03b1\u03c3"],
        "negative": ["\u03ba\u03b9\u03bd\u03b4\u03c5\u03bd", "\u03ba\u03c1\u03b9\u03c4\u03b9\u03ba", "\u03bc\u03b5\u03c1\u03bf\u03bb\u03b7\u03c8", "\u03b9\u03b4\u03b9\u03c9\u03c4\u03b9\u03ba", "\u03c0\u03b1\u03c1\u03b1\u03b2\u03b9\u03b1\u03c3", "\u03c0\u03b1\u03c1\u03b1\u03c0\u03bb\u03b7\u03c1"],
    },
    "he": {
        "positive": ["\u05d0\u05d7\u05e8\u05d0\u05d9", "\u05d0\u05de\u05d9\u05df", "\u05d1\u05d8\u05d5\u05d7", "\u05e9\u05e7\u05d5\u05e3", "\u05d4\u05d2\u05e0\u05d4"],
        "negative": ["\u05e1\u05d9\u05db\u05d5\u05df", "\u05d1\u05d9\u05e7\u05d5\u05e8\u05ea", "\u05d4\u05d8\u05d9\u05d4", "\u05e4\u05e8\u05d8\u05d9\u05d5\u05ea", "\u05d4\u05e4\u05e8\u05d4", "\u05d3\u05d9\u05e1\u05d0\u05d9\u05e0\u05e4\u05d5\u05e8\u05de\u05e6\u05d9\u05d4"],
    },
    "fa": {
        "positive": ["\u0645\u0633\u0626\u0648\u0644", "\u0642\u0627\u0628\u0644 \u0627\u0639\u062a\u0645\u0627\u062f", "\u0627\u06cc\u0645\u0646", "\u0634\u0641\u0627\u0641", "\u062d\u0641\u0627\u0638\u062a"],
        "negative": ["\u062e\u0637\u0631", "\u0627\u0646\u062a\u0642\u0627\u062f", "\u062a\u0628\u0639\u06cc\u0636", "\u062d\u0631\u06cc\u0645 \u062e\u0635\u0648\u0635\u06cc", "\u0646\u0642\u0636", "\u0627\u0637\u0644\u0627\u0639\u0627\u062a \u0646\u0627\u062f\u0631\u0633\u062a"],
    },
    "ur": {
        "positive": ["\u0630\u0645\u06c1 \u062f\u0627\u0631", "\u0642\u0627\u0628\u0644 \u0627\u0639\u062a\u0645\u0627\u062f", "\u0645\u062d\u0641\u0648\u0638", "\u0634\u0641\u0627\u0641", "\u062a\u062d\u0641\u0638"],
        "negative": ["\u062e\u0637\u0631\u06c1", "\u062a\u0646\u0642\u06cc\u062f", "\u062a\u0639\u0635\u0628", "\u0631\u0627\u0632\u062f\u0627\u0631\u06cc", "\u062e\u0644\u0627\u0641 \u0648\u0631\u0632\u06cc", "\u063a\u0644\u0637 \u0645\u0639\u0644\u0648\u0645\u0627\u062a"],
    },
    "id": {
        "positive": ["bertanggung jawab", "andal", "aman", "transparan", "perlindungan", "kepatuhan"],
        "negative": ["risiko", "kritik", "bias", "privasi", "pelanggaran", "disinformasi", "kontroversi"],
    },
    "ms": {
        "positive": ["bertanggungjawab", "dipercayai", "selamat", "telus", "perlindungan", "pematuhan"],
        "negative": ["risiko", "kritikan", "bias", "privasi", "pelanggaran", "disinformasi", "kontroversi"],
    },
    "th": {
        "positive": ["\u0e23\u0e31\u0e1a\u0e1c\u0e34\u0e14\u0e0a\u0e2d\u0e1a", "\u0e19\u0e48\u0e32\u0e40\u0e0a\u0e37\u0e48\u0e2d\u0e16\u0e37\u0e2d", "\u0e1b\u0e25\u0e2d\u0e14\u0e20\u0e31\u0e22", "\u0e42\u0e1b\u0e23\u0e48\u0e07\u0e43\u0e2a"],
        "negative": ["\u0e04\u0e27\u0e32\u0e21\u0e40\u0e2a\u0e35\u0e48\u0e22\u0e07", "\u0e27\u0e34\u0e08\u0e32\u0e23\u0e13\u0e4c", "\u0e2d\u0e04\u0e15\u0e34", "\u0e04\u0e27\u0e32\u0e21\u0e40\u0e1b\u0e47\u0e19\u0e2a\u0e48\u0e27\u0e19\u0e15\u0e31\u0e27", "\u0e25\u0e30\u0e40\u0e21\u0e34\u0e14"],
    },
    "vi": {
        "positive": ["trach nhiem", "dang tin cay", "an toan", "minh bach", "bao ve", "tuan thu"],
        "negative": ["rui ro", "chi trich", "thien vi", "quyen rieng tu", "vi pham", "tin gia", "tranh cai"],
    },
})


def normalise_text(value):
    return str(value or "").lower()


def keyword_hits(text, keywords):
    text = normalise_text(text)
    hits = []

    for keyword in keywords:
        if keyword.lower() in text:
            hits.append(keyword)

    return hits


def base_language_code(language_code="en"):
    profile = LANGUAGE_PROFILES.get(language_code, LANGUAGE_PROFILES["en"])
    return profile.get("base_language", language_code.split("_")[0])


def category_keywords(category, language_code="en"):
    base_language = base_language_code(language_code)
    localized = LOCALIZED_CATEGORY_KEYWORDS.get(base_language, {})

    if base_language == "en":
        return list(CATEGORY_KEYWORDS.get(category, []))

    return list(localized.get(category, [])) + list(CATEGORY_KEYWORDS.get(category, []))


def matching_categories(text, language_code="en"):
    matches = {}

    for category in CATEGORY_KEYWORDS:
        hits = keyword_hits(text, category_keywords(category, language_code))
        if hits:
            matches[category] = hits

    return matches


def sentiment_label(score):
    if score >= 0.3:
        return "Positive"
    if score <= -0.3:
        return "Negative"
    return "Neutral"


def score_multilingual_sentiment(text, language_code, analyzer):
    base_language = base_language_code(language_code)

    if base_language == "en":
        sentiment = analyzer.polarity_scores(text)["compound"]
        subjectivity = TextBlob(text).sentiment.subjectivity
        return (
            float(sentiment),
            float(subjectivity),
            sentiment_label(sentiment),
            "English VADER/TextBlob prototype",
        )

    lexicon = SENTIMENT_LEXICONS.get(base_language, {})
    positive_hits = keyword_hits(text, lexicon.get("positive", []))
    negative_hits = keyword_hits(text, lexicon.get("negative", []))

    positive_count = len(positive_hits)
    negative_count = len(negative_hits)
    total_count = positive_count + negative_count

    if total_count == 0:
        return (
            0.0,
            0.0,
            "Neutral",
            "Prototype multilingual lexicon sentiment; validation required",
        )

    sentiment = (positive_count - negative_count) / total_count
    subjectivity = min(1.0, total_count / 5)

    return (
        float(sentiment),
        float(subjectivity),
        sentiment_label(sentiment),
        "Prototype multilingual lexicon sentiment; validation required",
    )


def governance_risk_score(sentiment, subjectivity, category_count, risk_count, positive_count, language_code="en"):
    negative_component = max(0, -sentiment) * 45
    subjectivity_component = subjectivity * 20
    category_component = min(15, category_count * 4)
    risk_component = min(25, risk_count * 6)
    positive_offset = min(10, positive_count * 2)

    score = (
        negative_component
        + subjectivity_component
        + category_component
        + risk_component
        - positive_offset
    )

    return round(max(0, min(100, score)), 2)


def build_governance_query(entity_query, category, custom_terms=None, language_code="en"):
    keywords = category_keywords(category, language_code)

    if custom_terms:
        keywords = keywords + custom_terms

    quoted_terms = [
        f'"{term}"' if " " in term else term
        for term in keywords[:6]
    ]

    category_query = " OR ".join(quoted_terms)
    return f'"{entity_query}" ({category_query})'


def fetch_google_news(query, limit, language_code="en"):
    profile = LANGUAGE_PROFILES.get(language_code, LANGUAGE_PROFILES["en"])
    encoded_query = quote_plus(query)
    url = (
        "https://news.google.com/rss/search"
        f"?q={encoded_query}&hl={profile['hl']}&gl={profile['gl']}&ceid={profile['ceid']}"
    )

    try:
        response = requests.get(url, timeout=12)
        response.raise_for_status()
    except requests.RequestException:
        return []

    feed = feedparser.parse(response.content)

    rows = []

    for entry in feed.entries[:limit]:
        rows.append({
            "title": getattr(entry, "title", ""),
            "summary": getattr(entry, "summary", ""),
            "link": getattr(entry, "link", ""),
            "published": getattr(entry, "published", ""),
            "source": getattr(
                getattr(entry, "source", None),
                "title",
                "",
            ),
        })

    return rows


def collect_ai_governance_narratives(
    entity_name,
    short_name,
    entity_query,
    selected_categories,
    limit_per_category=15,
    strict_matching=True,
    custom_terms=None,
    language_codes=None,
    entity_aliases=None,
):
    analyzer = SentimentIntensityAnalyzer()
    rows = []
    seen = set()
    language_codes = language_codes or ["en"]
    entity_queries = [entity_query] + list(entity_aliases or [])

    for language_code in language_codes:
        profile = LANGUAGE_PROFILES.get(language_code, LANGUAGE_PROFILES["en"])

        for query_entity in entity_queries:
            if not str(query_entity).strip():
                continue

            for query_category in selected_categories:
                query = build_governance_query(
                    query_entity,
                    query_category,
                    custom_terms=custom_terms,
                    language_code=language_code,
                )

                for item in fetch_google_news(query, limit_per_category, language_code):
                    title = item["title"].strip()
                    combined_text = f'{title} {item["summary"]}'

                    if not title:
                        continue

                    dedupe_key = (language_code, title.lower(), item["link"])
                    if dedupe_key in seen:
                        continue

                    category_matches = matching_categories(combined_text, language_code)

                    if strict_matching and not category_matches:
                        continue

                    seen.add(dedupe_key)

                    if category_matches:
                        primary_category = (
                            query_category
                            if query_category in category_matches
                            else next(iter(category_matches))
                        )
                        matched_keywords = sorted({
                            keyword
                            for hits in category_matches.values()
                            for keyword in hits
                        })
                        matched_category_names = sorted(category_matches.keys())
                    else:
                        primary_category = query_category
                        matched_keywords = []
                        matched_category_names = [query_category]

                    sentiment, subjectivity, sentiment_status, sentiment_method = (
                        score_multilingual_sentiment(title, language_code, analyzer)
                    )

                    lexicon = SENTIMENT_LEXICONS.get(base_language_code(language_code), {})
                    risk_hits = keyword_hits(
                        combined_text,
                        RISK_TERMS + LOCALIZED_RISK_TERMS + lexicon.get("negative", []),
                    )
                    positive_hits = keyword_hits(
                        combined_text,
                        POSITIVE_GOVERNANCE_TERMS + lexicon.get("positive", []),
                    )
                    score = governance_risk_score(
                        sentiment=sentiment,
                        subjectivity=subjectivity,
                        category_count=len(matched_category_names),
                        risk_count=len(risk_hits),
                        positive_count=len(positive_hits),
                        language_code=language_code,
                    )

                    rows.append({
                        "Entity": entity_name,
                        "Short Name": short_name,
                        "Language": profile["label"],
                        "Language Code": language_code,
                        "Base Language": base_language_code(language_code),
                        "Edition Country": profile.get("country", ""),
                        "Edition Region": profile.get("region", ""),
                        "Edition ISO3": profile.get("iso3", ""),
                        "Edition Latitude": profile.get("latitude", 0),
                        "Edition Longitude": profile.get("longitude", 0),
                        "Sentiment Method": sentiment_method,
                        "Entity Query": query_entity,
                        "Primary Category": primary_category,
                        "Matched Categories": ", ".join(matched_category_names),
                        "Headline": title,
                        "Source": item["source"],
                        "Published": item["published"],
                        "Sentiment": round(float(sentiment), 3),
                        "Sentiment Label": sentiment_status,
                        "Subjectivity": round(float(subjectivity), 3),
                        "Governance Risk Score": score,
                        "Matched Keywords": ", ".join(matched_keywords),
                        "Risk Terms": ", ".join(risk_hits),
                        "Link": item["link"],
                        "Search Query": query,
                    })

    return rows
