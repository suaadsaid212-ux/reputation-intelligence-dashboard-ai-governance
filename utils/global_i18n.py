import copy
import pandas as pd
import streamlit as st

LANGUAGES = {
    "English": "en",
    "العربية": "ar",
    "Русский": "ru",
    "Français": "fr",
    "Español": "es",
    "Deutsch": "de",
}

LANGUAGE_NAMES = {
    "en": "English",
    "ar": "العربية",
    "ru": "Русский",
    "fr": "Français",
    "es": "Español",
    "de": "Deutsch",
}

PAGE_TITLES = {
    "en": {
        "home": "Home",
        "executive": "Executive Overview",
        "organization": "Organization Intelligence",
        "country": "Country Exposure",
        "narrative": "Narrative Intelligence",
        "sentiment": "Sentiment & Subjectivity",
        "rii": "Reputation Intelligence Index",
        "trends": "Google Trends Intelligence",
        "social": "Social Media Intelligence",
        "registry": "Organization Registry",
        "lifecycle": "Lifecycle Intelligence",
        "crisis": "Crisis Early Warning",
        "sector": "Sector Intelligence",
        "governance": "AI Governance & Reputation Intelligence",
        "omnichannel": "Omnichannel Social Intelligence",
        "verification": "Content Authenticity & Fact Verification",
    },
    "ar": {
        "home": "الرئيسية",
        "executive": "النظرة التنفيذية",
        "organization": "استخبارات المؤسسة",
        "country": "التعرض حسب الدولة",
        "narrative": "استخبارات السرديات",
        "sentiment": "تحليل المشاعر والذاتية",
        "rii": "مؤشر استخبارات السمعة",
        "trends": "استخبارات اتجاهات Google",
        "social": "استخبارات وسائل التواصل",
        "registry": "سجل المؤسسات",
        "lifecycle": "استخبارات دورة الحياة",
        "crisis": "الإنذار المبكر للأزمات",
        "sector": "استخبارات القطاع",
        "governance": "حوكمة الذكاء الاصطناعي واستخبارات السمعة",
        "omnichannel": "استخبارات التواصل متعددة المنصات",
        "verification": "التحقق من صحة المحتوى والحقائق",
    },
    "ru": {
        "home": "Главная",
        "executive": "Обзор для руководства",
        "organization": "Аналитика организации",
        "country": "Страновая экспозиция",
        "narrative": "Аналитика нарративов",
        "sentiment": "Тональность и субъективность",
        "rii": "Индекс репутационной аналитики",
        "trends": "Аналитика Google Trends",
        "social": "Аналитика социальных сетей",
        "registry": "Реестр организаций",
        "lifecycle": "Аналитика жизненного цикла",
        "crisis": "Раннее предупреждение кризиса",
        "sector": "Отраслевая аналитика",
        "governance": "Управление ИИ и репутационная аналитика",
        "omnichannel": "Омниканальная социальная аналитика",
        "verification": "Проверка достоверности и аутентичности контента",
    },
    "fr": {
        "home": "Accueil",
        "executive": "Vue d’ensemble exécutive",
        "organization": "Intelligence organisationnelle",
        "country": "Exposition par pays",
        "narrative": "Intelligence narrative",
        "sentiment": "Sentiment et subjectivité",
        "rii": "Indice d’intelligence de réputation",
        "trends": "Intelligence Google Trends",
        "social": "Intelligence des médias sociaux",
        "registry": "Registre des organisations",
        "lifecycle": "Intelligence du cycle de vie",
        "crisis": "Alerte précoce de crise",
        "sector": "Intelligence sectorielle",
        "governance": "Gouvernance de l’IA et intelligence de réputation",
        "omnichannel": "Intelligence sociale omnicanale",
        "verification": "Authenticité du contenu et vérification des faits",
    },
    "es": {
        "home": "Inicio",
        "executive": "Resumen ejecutivo",
        "organization": "Inteligencia de la organización",
        "country": "Exposición por país",
        "narrative": "Inteligencia narrativa",
        "sentiment": "Sentimiento y subjetividad",
        "rii": "Índice de inteligencia reputacional",
        "trends": "Inteligencia de Google Trends",
        "social": "Inteligencia de redes sociales",
        "registry": "Registro de organizaciones",
        "lifecycle": "Inteligencia del ciclo de vida",
        "crisis": "Alerta temprana de crisis",
        "sector": "Inteligencia sectorial",
        "governance": "Gobernanza de IA e inteligencia reputacional",
        "omnichannel": "Inteligencia social omnicanal",
        "verification": "Autenticidad del contenido y verificación de hechos",
    },
    "de": {
        "home": "Startseite",
        "executive": "Managementübersicht",
        "organization": "Organisationsanalyse",
        "country": "Länderexposition",
        "narrative": "Narrativanalyse",
        "sentiment": "Sentiment und Subjektivität",
        "rii": "Reputationsintelligenz-Index",
        "trends": "Google-Trends-Analyse",
        "social": "Social-Media-Analyse",
        "registry": "Organisationsregister",
        "lifecycle": "Lebenszyklusanalyse",
        "crisis": "Krisenfrühwarnung",
        "sector": "Sektoranalyse",
        "governance": "KI-Governance und Reputationsanalyse",
        "omnichannel": "Omnichannel Social Intelligence",
        "verification": "Inhaltsauthentizität und Faktenprüfung",
    },
}

# Display translations. Internal values remain unchanged.
COMMON = {
    "Analysis Period": {
        "ar": "فترة التحليل", "ru": "Период анализа", "fr": "Période d’analyse",
        "es": "Periodo de análisis", "de": "Analysezeitraum"
    },
    "Filter by Sector": {
        "ar": "التصفية حسب القطاع", "ru": "Фильтр по сектору", "fr": "Filtrer par secteur",
        "es": "Filtrar por sector", "de": "Nach Sektor filtern"
    },
    "Filter by Priority": {
        "ar": "التصفية حسب الأولوية", "ru": "Фильтр по приоритету", "fr": "Filtrer par priorité",
        "es": "Filtrar por prioridad", "de": "Nach Priorität filtern"
    },
    "Filter by Country": {
        "ar": "التصفية حسب الدولة", "ru": "Фильтр по стране", "fr": "Filtrer par pays",
        "es": "Filtrar por país", "de": "Nach Land filtern"
    },
    "Select Organizations": {
        "ar": "اختر المؤسسات", "ru": "Выберите организации", "fr": "Sélectionner les organisations",
        "es": "Seleccionar organizaciones", "de": "Organisationen auswählen"
    },
    "Select Entity": {
        "ar": "اختر الجهة", "ru": "Выберите объект", "fr": "Sélectionner l’entité",
        "es": "Seleccionar entidad", "de": "Entität auswählen"
    },
    "Entity": {"ar": "الجهة", "ru": "Объект", "fr": "Entité", "es": "Entidad", "de": "Entität"},
    "Entities": {"ar": "الجهات", "ru": "Объекты", "fr": "Entités", "es": "Entidades", "de": "Entitäten"},
    "Type": {"ar": "النوع", "ru": "Тип", "fr": "Type", "es": "Tipo", "de": "Typ"},
    "Country": {"ar": "الدولة", "ru": "Страна", "fr": "Pays", "es": "País", "de": "Land"},
    "Countries": {"ar": "الدول", "ru": "Страны", "fr": "Pays", "es": "Países", "de": "Länder"},
    "Sector": {"ar": "القطاع", "ru": "Сектор", "fr": "Secteur", "es": "Sector", "de": "Sektor"},
    "Sectors": {"ar": "القطاعات", "ru": "Секторы", "fr": "Secteurs", "es": "Sectores", "de": "Sektoren"},
    "Industry": {"ar": "الصناعة", "ru": "Отрасль", "fr": "Industrie", "es": "Industria", "de": "Branche"},
    "Priority": {"ar": "الأولوية", "ru": "Приоритет", "fr": "Priorité", "es": "Prioridad", "de": "Priorität"},
    "Language": {"ar": "اللغة", "ru": "Язык", "fr": "Langue", "es": "Idioma", "de": "Sprache"},
    "English": {"ar": "الإنجليزية", "ru": "Английский", "fr": "Anglais", "es": "Inglés", "de": "Englisch"},
    "Arabic": {"ar": "العربية", "ru": "Арабский", "fr": "Arabe", "es": "Árabe", "de": "Arabisch"},
    "Russian": {"ar": "الروسية", "ru": "Русский", "fr": "Russe", "es": "Ruso", "de": "Russisch"},
    "French": {"ar": "الفرنسية", "ru": "Французский", "fr": "Français", "es": "Francés", "de": "Französisch"},
    "Spanish": {"ar": "الإسبانية", "ru": "Испанский", "fr": "Espagnol", "es": "Español", "de": "Spanisch"},
    "German": {"ar": "الألمانية", "ru": "Немецкий", "fr": "Allemand", "es": "Alemán", "de": "Deutsch"},
    "1 Month": {"ar": "شهر واحد", "ru": "1 месяц", "fr": "1 mois", "es": "1 mes", "de": "1 Monat"},
    "3 Months": {"ar": "3 أشهر", "ru": "3 месяца", "fr": "3 mois", "es": "3 meses", "de": "3 Monate"},
    "6 Months": {"ar": "6 أشهر", "ru": "6 месяцев", "fr": "6 mois", "es": "6 meses", "de": "6 Monate"},
    "1 Year": {"ar": "سنة واحدة", "ru": "1 год", "fr": "1 an", "es": "1 año", "de": "1 Jahr"},
    "3 Years": {"ar": "3 سنوات", "ru": "3 года", "fr": "3 ans", "es": "3 años", "de": "3 Jahre"},
    "5 Years": {"ar": "5 سنوات", "ru": "5 лет", "fr": "5 ans", "es": "5 años", "de": "5 Jahre"},
    "High": {"ar": "مرتفع", "ru": "Высокий", "fr": "Élevé", "es": "Alto", "de": "Hoch"},
    "Medium": {"ar": "متوسط", "ru": "Средний", "fr": "Moyen", "es": "Medio", "de": "Mittel"},
    "Low": {"ar": "منخفض", "ru": "Низкий", "fr": "Faible", "es": "Bajo", "de": "Niedrig"},
    "Critical": {"ar": "حرج", "ru": "Критический", "fr": "Critique", "es": "Crítico", "de": "Kritisch"},
    "Stable": {"ar": "مستقر", "ru": "Стабильно", "fr": "Stable", "es": "Estable", "de": "Stabil"},
    "Monitor": {"ar": "مراقبة", "ru": "Наблюдать", "fr": "Surveiller", "es": "Supervisar", "de": "Beobachten"},
    "Elevated": {"ar": "مرتفع", "ru": "Повышенный", "fr": "Élevé", "es": "Elevado", "de": "Erhöht"},
    "High Risk": {"ar": "مخاطر مرتفعة", "ru": "Высокий риск", "fr": "Risque élevé", "es": "Riesgo alto", "de": "Hohes Risiko"},
    "Positive": {"ar": "إيجابي", "ru": "Позитивный", "fr": "Positif", "es": "Positivo", "de": "Positiv"},
    "Negative": {"ar": "سلبي", "ru": "Негативный", "fr": "Négatif", "es": "Negativo", "de": "Negativ"},
    "Neutral": {"ar": "محايد", "ru": "Нейтральный", "fr": "Neutre", "es": "Neutral", "de": "Neutral"},
    "Headline": {"ar": "العنوان", "ru": "Заголовок", "fr": "Titre", "es": "Titular", "de": "Überschrift"},
    "Sentiment": {"ar": "المشاعر", "ru": "Тональность", "fr": "Sentiment", "es": "Sentimiento", "de": "Sentiment"},
    "Subjectivity": {"ar": "الذاتية", "ru": "Субъективность", "fr": "Subjectivité", "es": "Subjetividad", "de": "Subjektivität"},
    "Reputation Risk": {"ar": "مخاطر السمعة", "ru": "Репутационный риск", "fr": "Risque de réputation", "es": "Riesgo reputacional", "de": "Reputationsrisiko"},
    "Risk Level": {"ar": "مستوى المخاطر", "ru": "Уровень риска", "fr": "Niveau de risque", "es": "Nivel de riesgo", "de": "Risikostufe"},
    "Rank": {"ar": "الترتيب", "ru": "Ранг", "fr": "Rang", "es": "Clasificación", "de": "Rang"},
    "Exposure": {"ar": "التعرض", "ru": "Экспозиция", "fr": "Exposition", "es": "Exposición", "de": "Exposition"},
    "Vulnerability": {"ar": "الهشاشة", "ru": "Уязвимость", "fr": "Vulnérabilité", "es": "Vulnerabilidad", "de": "Verwundbarkeit"},
    "Resilience": {"ar": "المرونة", "ru": "Устойчивость", "fr": "Résilience", "es": "Resiliencia", "de": "Resilienz"},
    "Platforms": {"ar": "المنصات", "ru": "Платформы", "fr": "Plateformes", "es": "Plataformas", "de": "Plattformen"},
    "Platform": {"ar": "المنصة", "ru": "Платформа", "fr": "Plateforme", "es": "Plataforma", "de": "Plattform"},
    "Mentions": {"ar": "الإشارات", "ru": "Упоминания", "fr": "Mentions", "es": "Menciones", "de": "Erwähnungen"},
    "Engagement": {"ar": "التفاعل", "ru": "Вовлечённость", "fr": "Engagement", "es": "Interacción", "de": "Interaktion"},
    "Source": {"ar": "المصدر", "ru": "Источник", "fr": "Source", "es": "Fuente", "de": "Quelle"},
    "Link": {"ar": "الرابط", "ru": "Ссылка", "fr": "Lien", "es": "Enlace", "de": "Link"},
    "Author": {"ar": "المؤلف", "ru": "Автор", "fr": "Auteur", "es": "Autor", "de": "Autor"},
    "Status": {"ar": "الحالة", "ru": "Статус", "fr": "Statut", "es": "Estado", "de": "Status"},
    "Confidence": {"ar": "الثقة", "ru": "Уверенность", "fr": "Confiance", "es": "Confianza", "de": "Konfidenz"},
    "Score": {"ar": "الدرجة", "ru": "Оценка", "fr": "Score", "es": "Puntuación", "de": "Wert"},
    "Similarity": {"ar": "التشابه", "ru": "Сходство", "fr": "Similarité", "es": "Similitud", "de": "Ähnlichkeit"},
}

HEADINGS = {
    "Executive Overview": {"ar": "النظرة التنفيذية", "ru": "Обзор для руководства", "fr": "Vue d’ensemble exécutive", "es": "Resumen ejecutivo", "de": "Managementübersicht"},
    "Organization Intelligence": {"ar": "استخبارات المؤسسة", "ru": "Аналитика организации", "fr": "Intelligence organisationnelle", "es": "Inteligencia de la organización", "de": "Organisationsanalyse"},
    "Country Exposure Intelligence": {"ar": "استخبارات التعرض حسب الدولة", "ru": "Аналитика страновой экспозиции", "fr": "Intelligence d’exposition par pays", "es": "Inteligencia de exposición por país", "de": "Länderexpositionsanalyse"},
    "Narrative Intelligence": {"ar": "استخبارات السرديات", "ru": "Аналитика нарративов", "fr": "Intelligence narrative", "es": "Inteligencia narrativa", "de": "Narrativanalyse"},
    "Sentiment & Subjectivity Intelligence": {"ar": "استخبارات المشاعر والذاتية", "ru": "Аналитика тональности и субъективности", "fr": "Intelligence du sentiment et de la subjectivité", "es": "Inteligencia de sentimiento y subjetividad", "de": "Sentiment- und Subjektivitätsanalyse"},
    "Reputation Intelligence Index (RII)": {"ar": "مؤشر استخبارات السمعة (RII)", "ru": "Индекс репутационной аналитики (RII)", "fr": "Indice d’intelligence de réputation (RII)", "es": "Índice de inteligencia reputacional (RII)", "de": "Reputationsintelligenz-Index (RII)"},
    "Google Trends Intelligence": {"ar": "استخبارات اتجاهات Google", "ru": "Аналитика Google Trends", "fr": "Intelligence Google Trends", "es": "Inteligencia de Google Trends", "de": "Google-Trends-Analyse"},
    "Social Media Intelligence": {"ar": "استخبارات وسائل التواصل", "ru": "Аналитика социальных сетей", "fr": "Intelligence des médias sociaux", "es": "Inteligencia de redes sociales", "de": "Social-Media-Analyse"},
    "Organization Registry": {"ar": "سجل المؤسسات", "ru": "Реестр организаций", "fr": "Registre des organisations", "es": "Registro de organizaciones", "de": "Organisationsregister"},
    "Organization Lifecycle Intelligence": {"ar": "استخبارات دورة حياة المؤسسة", "ru": "Аналитика жизненного цикла организации", "fr": "Intelligence du cycle de vie de l’organisation", "es": "Inteligencia del ciclo de vida organizacional", "de": "Analyse des Organisationslebenszyklus"},
    "Crisis Early Warning": {"ar": "الإنذار المبكر للأزمات", "ru": "Раннее предупреждение кризиса", "fr": "Alerte précoce de crise", "es": "Alerta temprana de crisis", "de": "Krisenfrühwarnung"},
    "Sector Intelligence": {"ar": "استخبارات القطاع", "ru": "Отраслевая аналитика", "fr": "Intelligence sectorielle", "es": "Inteligencia sectorial", "de": "Sektoranalyse"},
    "AI Governance & Reputation Intelligence": {"ar": "حوكمة الذكاء الاصطناعي واستخبارات السمعة", "ru": "Управление ИИ и репутационная аналитика", "fr": "Gouvernance de l’IA et intelligence de réputation", "es": "Gobernanza de IA e inteligencia reputacional", "de": "KI-Governance und Reputationsanalyse"},
    "Omnichannel Social Intelligence": {"ar": "استخبارات التواصل متعددة المنصات", "ru": "Омниканальная социальная аналитика", "fr": "Intelligence sociale omnicanale", "es": "Inteligencia social omnicanal", "de": "Omnichannel Social Intelligence"},
    "Content Authenticity & Fact Verification": {"ar": "التحقق من صحة المحتوى والحقائق", "ru": "Проверка достоверности и аутентичности контента", "fr": "Authenticité du contenu et vérification des faits", "es": "Autenticidad del contenido y verificación de hechos", "de": "Inhaltsauthentizität und Faktenprüfung"},
    "Organization Risk Ranking": {"ar": "ترتيب مخاطر المؤسسات", "ru": "Рейтинг риска организаций", "fr": "Classement du risque des organisations", "es": "Clasificación de riesgo de organizaciones", "de": "Risikorangliste der Organisationen"},
    "Risk Alert Engine": {"ar": "محرك تنبيهات المخاطر", "ru": "Система предупреждений о риске", "fr": "Moteur d’alerte de risque", "es": "Motor de alertas de riesgo", "de": "Risikowarnsystem"},
    "Top Negative Narratives": {"ar": "أبرز السرديات السلبية", "ru": "Наиболее негативные нарративы", "fr": "Principaux récits négatifs", "es": "Principales narrativas negativas", "de": "Wichtigste negative Narrative"},
    "News and Sentiment": {"ar": "الأخبار والمشاعر", "ru": "Новости и тональность", "fr": "Actualités et sentiment", "es": "Noticias y sentimiento", "de": "Nachrichten und Sentiment"},
    "Sentiment Distribution": {"ar": "توزيع المشاعر", "ru": "Распределение тональности", "fr": "Distribution du sentiment", "es": "Distribución del sentimiento", "de": "Sentimentverteilung"},
    "Country Exposure Summary": {"ar": "ملخص التعرض حسب الدولة", "ru": "Сводка страновой экспозиции", "fr": "Résumé de l’exposition par pays", "es": "Resumen de exposición por país", "de": "Zusammenfassung der Länderexposition"},
    "Country Risk Ranking": {"ar": "ترتيب المخاطر حسب الدولة", "ru": "Рейтинг странового риска", "fr": "Classement du risque pays", "es": "Clasificación de riesgo por país", "de": "Länderrisikorangliste"},
    "Geographic Country Risk Map": {"ar": "الخريطة الجغرافية لمخاطر الدول", "ru": "Географическая карта странового риска", "fr": "Carte géographique du risque pays", "es": "Mapa geográfico de riesgo por país", "de": "Geografische Länderrisikokarte"},
    "Narrative Feed": {"ar": "تدفق السرديات", "ru": "Лента нарративов", "fr": "Flux de récits", "es": "Flujo de narrativas", "de": "Narrativ-Feed"},
    "High-Risk Narratives": {"ar": "السرديات عالية المخاطر", "ru": "Нарративы высокого риска", "fr": "Récits à risque élevé", "es": "Narrativas de alto riesgo", "de": "Narrative mit hohem Risiko"},
    "Narrative Risk Distribution": {"ar": "توزيع مخاطر السرديات", "ru": "Распределение риска нарративов", "fr": "Distribution du risque narratif", "es": "Distribución del riesgo narrativo", "de": "Verteilung des Narrativrisikos"},
    "Executive Reputation KPIs": {"ar": "مؤشرات السمعة التنفيذية", "ru": "Ключевые показатели репутации", "fr": "Indicateurs clés de réputation", "es": "Indicadores ejecutivos de reputación", "de": "Reputations-KPIs"},
    "Latest News Headlines": {"ar": "أحدث عناوين الأخبار", "ru": "Последние новостные заголовки", "fr": "Derniers titres d’actualité", "es": "Últimos titulares", "de": "Neueste Schlagzeilen"},
    "Search Interest Timeline": {"ar": "الخط الزمني لاهتمام البحث", "ru": "Динамика поискового интереса", "fr": "Évolution de l’intérêt de recherche", "es": "Evolución del interés de búsqueda", "de": "Verlauf des Suchinteresses"},
    "Source Coverage": {"ar": "تغطية المصادر", "ru": "Покрытие источников", "fr": "Couverture des sources", "es": "Cobertura de fuentes", "de": "Quellenabdeckung"},
    "Platform Comparison": {"ar": "مقارنة المنصات", "ru": "Сравнение платформ", "fr": "Comparaison des plateformes", "es": "Comparación de plataformas", "de": "Plattformvergleich"},
    "Trending Social Narratives": {"ar": "السرديات الاجتماعية الرائجة", "ru": "Трендовые социальные нарративы", "fr": "Récits sociaux en tendance", "es": "Narrativas sociales en tendencia", "de": "Trendende Social-Narrative"},
    "Connector Readiness": {"ar": "جاهزية الربط", "ru": "Готовность коннекторов", "fr": "Préparation des connecteurs", "es": "Preparación de conectores", "de": "Connector-Bereitschaft"},
    "Executive Insight": {"ar": "الرؤية التنفيذية", "ru": "Вывод для руководства", "fr": "Synthèse exécutive", "es": "Conclusión ejecutiva", "de": "Managementeinsicht"},
    "Entity Profile": {"ar": "ملف الجهة", "ru": "Профиль объекта", "fr": "Profil de l’entité", "es": "Perfil de entidad", "de": "Entitätsprofil"},
    "Lifecycle Stage": {"ar": "مرحلة دورة الحياة", "ru": "Стадия жизненного цикла", "fr": "Étape du cycle de vie", "es": "Etapa del ciclo de vida", "de": "Lebenszyklusphase"},
    "Risk Breakdown": {"ar": "تفصيل المخاطر", "ru": "Структура риска", "fr": "Répartition du risque", "es": "Desglose del riesgo", "de": "Risikoaufschlüsselung"},
    "Threat Matrix": {"ar": "مصفوفة التهديد", "ru": "Матрица угроз", "fr": "Matrice des menaces", "es": "Matriz de amenazas", "de": "Bedrohungsmatrix"},
    "Recommended Actions": {"ar": "الإجراءات الموصى بها", "ru": "Рекомендуемые действия", "fr": "Actions recommandées", "es": "Acciones recomendadas", "de": "Empfohlene Maßnahmen"},
    "Sector Overview": {"ar": "نظرة عامة على القطاع", "ru": "Обзор сектора", "fr": "Vue d’ensemble du secteur", "es": "Resumen del sector", "de": "Sektorübersicht"},
    "Sector Benchmark": {"ar": "المعيار القطاعي", "ru": "Секторный бенчмарк", "fr": "Référence sectorielle", "es": "Referencia sectorial", "de": "Sektorbenchmark"},
    "Sector Ranking": {"ar": "ترتيب القطاع", "ru": "Рейтинг сектора", "fr": "Classement sectoriel", "es": "Clasificación sectorial", "de": "Sektorrangliste"},
    "Entity Comparison": {"ar": "مقارنة الجهات", "ru": "Сравнение объектов", "fr": "Comparaison des entités", "es": "Comparación de entidades", "de": "Entitätsvergleich"},
    "Geographic Narrative Exposure": {"ar": "التعرض الجغرافي للسرديات", "ru": "Географическая экспозиция нарративов", "fr": "Exposition géographique des récits", "es": "Exposición geográfica de narrativas", "de": "Geografische Narrativexposition"},
    "Source Coverage & Connector Readiness": {"ar": "تغطية المصادر وجاهزية الربط", "ru": "Покрытие источников и готовность коннекторов", "fr": "Couverture des sources et préparation des connecteurs", "es": "Cobertura de fuentes y preparación de conectores", "de": "Quellenabdeckung und Connector-Bereitschaft"},
    "Cross-Platform Executive Overview": {"ar": "نظرة تنفيذية عبر المنصات", "ru": "Межплатформенный обзор", "fr": "Vue d’ensemble multiplateforme", "es": "Resumen multiplataforma", "de": "Plattformübergreifende Übersicht"},
    "Platform Risk Comparison": {"ar": "مقارنة مخاطر المنصات", "ru": "Сравнение риска платформ", "fr": "Comparaison du risque par plateforme", "es": "Comparación de riesgo por plataforma", "de": "Plattformrisikovergleich"},
    "Cross-Platform Narrative Overlap": {"ar": "تداخل السرديات بين المنصات", "ru": "Пересечение нарративов", "fr": "Recoupement des récits entre plateformes", "es": "Coincidencia narrativa entre plataformas", "de": "Plattformübergreifende Narrativüberschneidung"},
    "High-Risk Social Narratives": {"ar": "السرديات الاجتماعية الأعلى خطراً", "ru": "Социальные нарративы высокого риска", "fr": "Récits sociaux à risque élevé", "es": "Narrativas sociales de alto riesgo", "de": "Social-Narrative mit hohem Risiko"},
    "Verification Decision": {"ar": "نتيجة التحقق", "ru": "Решение по проверке", "fr": "Décision de vérification", "es": "Decisión de verificación", "de": "Prüfentscheidung"},
    "Corroborating Evidence": {"ar": "الأدلة المؤيدة", "ru": "Подтверждающие данные", "fr": "Preuves corroborantes", "es": "Evidencia corroborante", "de": "Bestätigende Belege"},
    "Source Evidence": {"ar": "أدلة المصدر", "ru": "Данные источника", "fr": "Éléments de la source", "es": "Evidencia de la fuente", "de": "Quellenbelege"},
    "Synthetic-Origin Assessment": {"ar": "تقييم المنشأ الاصطناعي", "ru": "Оценка синтетического происхождения", "fr": "Évaluation de l’origine synthétique", "es": "Evaluación de origen sintético", "de": "Bewertung synthetischer Herkunft"},
    "Uploaded Image Provenance": {"ar": "منشأ الصورة المرفوعة", "ru": "Происхождение загруженного изображения", "fr": "Provenance de l’image téléversée", "es": "Procedencia de la imagen subida", "de": "Herkunft des hochgeladenen Bildes"},
}

TRANSLATIONS = {"en": {}}
for lang in ("ar", "ru", "fr", "es", "de"):
    mapping = {}
    for source, values in COMMON.items():
        if lang in values:
            mapping[source] = values[lang]
    for source, values in HEADINGS.items():
        if lang in values:
            mapping[source] = values[lang]
    TRANSLATIONS[lang] = mapping

def get_language():
    return st.session_state.get("trustintel_language", "en")

def page_title(page_key, lang=None):
    lang = lang or get_language()
    return PAGE_TITLES.get(lang, PAGE_TITLES["en"]).get(
        page_key, PAGE_TITLES["en"].get(page_key, page_key)
    )

def translate(text, lang=None):
    if not isinstance(text, str):
        return text
    lang = lang or get_language()
    if lang == "en":
        return text
    mapping = TRANSLATIONS.get(lang, {})
    if text in mapping:
        return mapping[text]
    result = text
    for source in sorted(mapping.keys(), key=len, reverse=True):
        if len(source) >= 8 and source in result:
            result = result.replace(source, mapping[source])
    return result

def translate_dataframe(data, lang=None):
    if not isinstance(data, pd.DataFrame):
        return data
    lang = lang or get_language()
    if lang == "en":
        return data
    result = data.copy()
    result.columns = [translate(str(col), lang) for col in result.columns]
    for col in result.columns:
        if result[col].dtype == object:
            result[col] = result[col].map(
                lambda v: translate(v, lang)
                if isinstance(v, str) and len(v) <= 80 else v
            )
    return result

def apply_direction(lang=None):
    lang = lang or get_language()
    if lang == "ar":
        st.markdown(
            """
            <style>
            [data-testid="stSidebar"] label,
            [data-testid="stSidebar"] p,
            [data-testid="stSidebar"] .stMarkdown,
            [data-testid="stMain"] .stMarkdown,
            [data-testid="stMain"] label,
            [data-testid="stMain"] input,
            [data-testid="stMain"] textarea {
                direction: rtl;
                text-align: right;
            }
            </style>
            """,
            unsafe_allow_html=True,
        )

def language_selector():
    code = st.session_state.get("trustintel_language", "en")
    current_name = LANGUAGE_NAMES.get(code, "English")
    names = list(LANGUAGES.keys())
    index = names.index(current_name) if current_name in names else 0
    selected = st.sidebar.selectbox(
        "🌐 Language | اللغة | Язык | Langue | Idioma | Sprache",
        names,
        index=index,
        key="trustintel_global_language_selector",
    )
    code = LANGUAGES[selected]
    st.session_state["trustintel_language"] = code
    apply_direction(code)
    return code

_PATCHED = False

def _translated_format_func(original=None):
    base = original or str
    return lambda value: translate(base(value))

def _translate_first(args, kwargs):
    args = list(args)
    if args and isinstance(args[0], str):
        args[0] = translate(args[0])
    for key in ("label", "help", "placeholder"):
        if isinstance(kwargs.get(key), str):
            kwargs[key] = translate(kwargs[key])
    return tuple(args), kwargs

def _translate_plotly(fig):
    try:
        out = copy.deepcopy(fig)
        if getattr(out.layout, "title", None) and getattr(out.layout.title, "text", None):
            out.layout.title.text = translate(out.layout.title.text)
        for axis_name in ("xaxis", "yaxis", "xaxis2", "yaxis2"):
            axis = getattr(out.layout, axis_name, None)
            if axis and getattr(axis, "title", None) and getattr(axis.title, "text", None):
                axis.title.text = translate(axis.title.text)
        for trace in out.data:
            if getattr(trace, "name", None):
                trace.name = translate(trace.name)
        return out
    except Exception:
        return fig

def _translate_matplotlib(fig):
    try:
        for axis in fig.get_axes():
            axis.set_title(translate(axis.get_title()))
            axis.set_xlabel(translate(axis.get_xlabel()))
            axis.set_ylabel(translate(axis.get_ylabel()))
        return fig
    except Exception:
        return fig

def install_global_translation():
    global _PATCHED
    if _PATCHED:
        return

    from streamlit.delta_generator import DeltaGenerator

    # IMPORTANT:
    # Every wrapper captures its original Streamlit function through a
    # factory argument. This prevents Python's late-binding closure behavior
    # from making one wrapper accidentally call a different Streamlit method.

    text_methods = [
        "title",
        "header",
        "subheader",
        "caption",
        "info",
        "warning",
        "success",
        "error",
        "markdown",
        "toast",
        "spinner",
        "expander",
        "popover",
    ]

    def make_dg_text_wrapper(func):
        def wrapper(self, *args, **kwargs):
            args, kwargs = _translate_first(args, kwargs)
            return func(self, *args, **kwargs)
        return wrapper

    def make_st_text_wrapper(func):
        def wrapper(*args, **kwargs):
            args, kwargs = _translate_first(args, kwargs)
            return func(*args, **kwargs)
        return wrapper

    for name in text_methods:
        if hasattr(DeltaGenerator, name):
            func = getattr(DeltaGenerator, name)
            setattr(
                DeltaGenerator,
                name,
                make_dg_text_wrapper(func),
            )

        if hasattr(st, name):
            func = getattr(st, name)
            setattr(
                st,
                name,
                make_st_text_wrapper(func),
            )

    # st.write / container.write
    if hasattr(DeltaGenerator, "write"):
        dg_write_original = DeltaGenerator.write

        def make_dg_write_wrapper(func):
            def wrapper(self, *args, **kwargs):
                translated_args = tuple(
                    translate(value)
                    if isinstance(value, str)
                    else value
                    for value in args
                )
                return func(
                    self,
                    *translated_args,
                    **kwargs,
                )
            return wrapper

        DeltaGenerator.write = make_dg_write_wrapper(
            dg_write_original
        )

    if hasattr(st, "write"):
        st_write_original = st.write

        def make_st_write_wrapper(func):
            def wrapper(*args, **kwargs):
                translated_args = tuple(
                    translate(value)
                    if isinstance(value, str)
                    else value
                    for value in args
                )
                return func(
                    *translated_args,
                    **kwargs,
                )
            return wrapper

        st.write = make_st_write_wrapper(
            st_write_original
        )

    # Metric
    if hasattr(DeltaGenerator, "metric"):
        metric_original = DeltaGenerator.metric

        def make_metric_wrapper(func):
            def wrapper(
                self,
                label,
                value,
                *args,
                **kwargs,
            ):
                label = translate(label)

                if isinstance(value, str):
                    value = translate(value)

                if isinstance(
                    kwargs.get("help"),
                    str,
                ):
                    kwargs["help"] = translate(
                        kwargs["help"]
                    )

                return func(
                    self,
                    label,
                    value,
                    *args,
                    **kwargs,
                )
            return wrapper

        DeltaGenerator.metric = make_metric_wrapper(
            metric_original
        )

    # Widgets
    widget_methods = [
        "selectbox",
        "multiselect",
        "radio",
        "text_input",
        "text_area",
        "number_input",
        "slider",
        "checkbox",
        "toggle",
        "button",
        "file_uploader",
        "date_input",
        "time_input",
    ]

    def make_widget_wrapper(
        func,
        method_name,
    ):
        def wrapper(
            self,
            *args,
            **kwargs,
        ):
            args, kwargs = _translate_first(
                args,
                kwargs,
            )

            if method_name in {
                "selectbox",
                "multiselect",
                "radio",
            }:
                existing = kwargs.get(
                    "format_func"
                )

                kwargs[
                    "format_func"
                ] = _translated_format_func(
                    existing
                )

            return func(
                self,
                *args,
                **kwargs,
            )

        return wrapper

    for name in widget_methods:
        if hasattr(
            DeltaGenerator,
            name,
        ):
            func = getattr(
                DeltaGenerator,
                name,
            )

            setattr(
                DeltaGenerator,
                name,
                make_widget_wrapper(
                    func,
                    name,
                ),
            )

    # Dataframes / tables
    def make_data_wrapper(func):
        def wrapper(
            self,
            data=None,
            *args,
            **kwargs,
        ):
            return func(
                self,
                translate_dataframe(data),
                *args,
                **kwargs,
            )
        return wrapper

    for name in (
        "dataframe",
        "table",
    ):
        if hasattr(
            DeltaGenerator,
            name,
        ):
            func = getattr(
                DeltaGenerator,
                name,
            )

            setattr(
                DeltaGenerator,
                name,
                make_data_wrapper(func),
            )

    # Plotly
    if hasattr(
        DeltaGenerator,
        "plotly_chart",
    ):
        plotly_original = (
            DeltaGenerator.plotly_chart
        )

        def make_plotly_wrapper(func):
            def wrapper(
                self,
                fig,
                *args,
                **kwargs,
            ):
                return func(
                    self,
                    _translate_plotly(fig),
                    *args,
                    **kwargs,
                )
            return wrapper

        DeltaGenerator.plotly_chart = (
            make_plotly_wrapper(
                plotly_original
            )
        )

    # Matplotlib
    if hasattr(
        DeltaGenerator,
        "pyplot",
    ):
        pyplot_original = (
            DeltaGenerator.pyplot
        )

        def make_pyplot_wrapper(func):
            def wrapper(
                self,
                fig=None,
                *args,
                **kwargs,
            ):
                if fig is not None:
                    fig = (
                        _translate_matplotlib(
                            fig
                        )
                    )

                return func(
                    self,
                    fig,
                    *args,
                    **kwargs,
                )
            return wrapper

        DeltaGenerator.pyplot = (
            make_pyplot_wrapper(
                pyplot_original
            )
        )

    # Page title translation
    if hasattr(
        st,
        "set_page_config",
    ):
        config_original = (
            st.set_page_config
        )

        def make_config_wrapper(func):
            def wrapper(
                *args,
                **kwargs,
            ):
                if isinstance(
                    kwargs.get(
                        "page_title"
                    ),
                    str,
                ):
                    kwargs[
                        "page_title"
                    ] = translate(
                        kwargs[
                            "page_title"
                        ]
                    )

                return func(
                    *args,
                    **kwargs,
                )
            return wrapper

        st.set_page_config = (
            make_config_wrapper(
                config_original
            )
        )

    _PATCHED = True
