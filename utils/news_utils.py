from utils.multilingual_content import (
    fetch_multilingual_news,
    get_selected_content_languages,
)


def get_news(
    query,
    limit=20,
    languages=None,
):
    languages = (
        languages
        or get_selected_content_languages()
    )

    per_language = max(
        2,
        int(
            limit
            / max(
                1,
                len(languages),
            )
        ),
    )

    df = fetch_multilingual_news(
        query=query,
        languages=languages,
        limit_per_language=per_language,
    )

    if df.empty:
        return []

    return [
        {
            "title":
            row["Headline"],
            "link":
            row["Link"],
            "published":
            row["Published"],
            "source":
            row["Source"],
            "language":
            row["Language"],
            "edition_country":
            row[
                "Edition Country"
            ],
            "sentiment":
            row["Sentiment"],
            "sentiment_method":
            row[
                "Sentiment Method"
            ],
            "sentiment_confidence":
            row[
                "Sentiment Confidence"
            ],
        }
        for _, row
        in df.head(
            limit
        ).iterrows()
    ]
