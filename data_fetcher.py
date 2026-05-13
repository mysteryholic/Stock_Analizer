"""
StockInsight Omni - 데이터 수집 모듈
yfinance 기반 주식 데이터 수집, 캐싱, 에러 핸들링
"""
import streamlit as st
import yfinance as yf
import pandas as pd
from datetime import datetime, timedelta
from config import MARKET_INDICES, INTERVAL_MAP


@st.cache_data(ttl=300, show_spinner=False)
def get_stock_data(ticker: str, period: str = "1y") -> pd.DataFrame:
    """주식 히스토리컬 데이터 수집 (5분 캐싱)"""
    try:
        interval = INTERVAL_MAP.get(period, "1d")
        stock = yf.Ticker(ticker)
        df = stock.history(period=period, interval=interval)
        if df.empty:
            return pd.DataFrame()
        df.index = pd.to_datetime(df.index)
        if df.columns.nlevels > 1:
            df.columns = df.columns.get_level_values(0)
        return df
    except Exception as e:
        st.warning(f"⚠️ {ticker} 데이터 수집 실패: {str(e)}")
        return pd.DataFrame()


@st.cache_data(ttl=120, show_spinner=False)
def get_market_indices() -> dict:
    """주요 시장 지수 현재 데이터 수집 (2분 캐싱)"""
    results = {}
    for name, info in MARKET_INDICES.items():
        try:
            stock = yf.Ticker(info["ticker"])
            hist = stock.history(period="5d")
            if hist.empty or len(hist) < 2:
                continue
            if hist.columns.nlevels > 1:
                hist.columns = hist.columns.get_level_values(0)
            current = float(hist["Close"].iloc[-1])
            previous = float(hist["Close"].iloc[-2])
            change = current - previous
            change_pct = (change / previous) * 100
            results[name] = {
                "current": current,
                "change": change,
                "change_pct": change_pct,
                "flag": info["flag"],
                "name": info["name"],
            }
        except Exception:
            continue
    return results


@st.cache_data(ttl=300, show_spinner=False)
def get_stock_info(ticker: str) -> dict:
    """기업 기본 정보 수집"""
    try:
        stock = yf.Ticker(ticker)
        info = stock.info
        return {
            "name": info.get("shortName", info.get("longName", ticker)),
            "sector": info.get("sector", "N/A"),
            "industry": info.get("industry", "N/A"),
            "market_cap": info.get("marketCap", 0),
            "per": info.get("trailingPE", None),
            "pbr": info.get("priceToBook", None),
            "dividend_yield": info.get("dividendYield", None),
            "52w_high": info.get("fiftyTwoWeekHigh", None),
            "52w_low": info.get("fiftyTwoWeekLow", None),
            "current_price": info.get("currentPrice", info.get("regularMarketPrice", None)),
            "volume": info.get("volume", info.get("regularMarketVolume", 0)),
            "avg_volume": info.get("averageVolume", 0),
            "description": info.get("longBusinessSummary", ""),
            "currency": info.get("currency", "USD"),
        }
    except Exception as e:
        return {"name": ticker, "error": str(e)}


@st.cache_data(ttl=600, show_spinner=False)
def get_financial_statements(ticker: str) -> dict:
    """재무제표 데이터 수집 (10분 캐싱)"""
    try:
        stock = yf.Ticker(ticker)
        result = {}
        income = stock.financials
        if income is not None and not income.empty:
            result["income_statement"] = income
        balance = stock.balance_sheet
        if balance is not None and not balance.empty:
            result["balance_sheet"] = balance
        cashflow = stock.cashflow
        if cashflow is not None and not cashflow.empty:
            result["cashflow"] = cashflow
        return result
    except Exception as e:
        return {"error": str(e)}


@st.cache_data(ttl=300, show_spinner=False)
def get_watchlist_data(tickers: list) -> list:
    """관심 종목 리스트 데이터 일괄 수집"""
    results = []
    for item in tickers:
        try:
            ticker = item["ticker"]
            stock = yf.Ticker(ticker)
            hist = stock.history(period="5d")
            if hist.empty:
                continue
            if hist.columns.nlevels > 1:
                hist.columns = hist.columns.get_level_values(0)
            current = float(hist["Close"].iloc[-1])
            previous = float(hist["Close"].iloc[-2]) if len(hist) >= 2 else current
            change_pct = ((current - previous) / previous) * 100 if previous != 0 else 0
            volume = int(hist["Volume"].iloc[-1]) if "Volume" in hist.columns else 0
            info = stock.info
            results.append({
                "name": item["name"],
                "ticker": ticker,
                "price": current,
                "change_pct": change_pct,
                "volume": volume,
                "high_52w": info.get("fiftyTwoWeekHigh", None),
                "low_52w": info.get("fiftyTwoWeekLow", None),
                "currency": info.get("currency", ""),
            })
        except Exception:
            continue
    return results


def format_number(num, currency=""):
    """숫자 포맷팅 (억, 조 단위)"""
    if num is None:
        return "N/A"
    if currency in ["KRW", ""] and num >= 1_0000_0000_0000:
        return f"₩{num / 1_0000_0000_0000:.1f}조"
    elif currency in ["KRW", ""] and num >= 1_0000_0000:
        return f"₩{num / 1_0000_0000:.0f}억"
    elif num >= 1_000_000_000_000:
        return f"${num / 1_000_000_000_000:.2f}T"
    elif num >= 1_000_000_000:
        return f"${num / 1_000_000_000:.2f}B"
    elif num >= 1_000_000:
        return f"${num / 1_000_000:.2f}M"
    else:
        return f"{num:,.0f}"


def format_price(price, currency="USD"):
    """가격 포맷팅"""
    if price is None:
        return "N/A"
    if currency == "KRW":
        return f"₩{price:,.0f}"
    return f"${price:,.2f}"
