import yfinance as yf


def get_stock_info(ticker):
    ticker = str(ticker).strip()

    if not ticker or ticker.lower() == "nan":
        return None

    try:
        stock = yf.Ticker(ticker)
        info = stock.info

        if not info:
            return None

        return {
            "name": info.get("longName"),
            "sector": info.get("sector"),
            "industry": info.get("industry"),
            "country": info.get("country"),
            "marketCap": info.get("marketCap"),
            "currency": info.get("currency"),
            "exchange": info.get("exchange"),
        }

    except Exception:
        return None
