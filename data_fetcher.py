"""
StockInsight Omni - 데이터 수집 모듈
yfinance 기반 주식 데이터 수집, 캐싱, 에러 핸들링
"""
import streamlit as st
import yfinance as yf
import pandas as pd
import concurrent.futures
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
    """관심 종목 리스트 데이터 초고속 일괄 수집 + 시총 정렬 (레이트리밋 내성형 배치 모드)"""
    if not tickers:
        return []
        
    results = []
    ticker_symbols = [item["ticker"] for item in tickers]
    
    # 1. 시세 병렬 배치 취득 (최신 주가, 변동률, 거래량)
    try:
        df = yf.download(ticker_symbols, period="5d", group_by='ticker', auto_adjust=True, progress=False)
    except Exception:
        return []

    # 2. 병렬 연산 스레드로 각 종목의 fast_info.market_cap 과 currency 확보 (속도 극대화)
    market_cap_map = {}
    currency_map = {}
    
    def fetch_fast_info(sym):
        try:
            fast = yf.Ticker(sym).fast_info
            return sym, fast.market_cap, fast.currency
        except Exception:
            return sym, 0, ""

    with concurrent.futures.ThreadPoolExecutor(max_workers=min(len(ticker_symbols), 10)) as executor:
        future_results = list(executor.map(fetch_fast_info, ticker_symbols))
        
    for sym, mcap, cur in future_results:
        market_cap_map[sym] = mcap or 0
        currency_map[sym] = cur or ""

    # 3. 다중 인덱스 데이터프레임 파싱 및 조립
    for item in tickers:
        sym = item["ticker"]
        try:
            if sym not in df.columns.get_level_values(0):
                continue
                
            # 특정 주식의 시세 히스토리 추출 및 결측치 소거
            ticker_df = df[sym].dropna(subset=["Close"])
            if ticker_df.empty:
                continue
            
            current = float(ticker_df["Close"].iloc[-1])
            previous = float(ticker_df["Close"].iloc[-2]) if len(ticker_df) >= 2 else current
            change_pct = ((current - previous) / previous) * 100 if previous != 0 else 0
            volume = int(ticker_df["Volume"].iloc[-1]) if "Volume" in ticker_df.columns else 0
            
            # 실시간 가격, 거래량에 획득한 시총 및 통화코드 결합
            results.append({
                "name": item["name"],
                "ticker": sym,
                "price": current,
                "change_pct": change_pct,
                "volume": volume,
                "market_cap": market_cap_map.get(sym, 0),
                "currency": currency_map.get(sym, ""),
            })
        except Exception:
            continue
            
    # 4. 시가총액(market_cap) 기준 실시간 내림차순 완벽 자동 정렬 구현 (요구사항 반영)
    results.sort(key=lambda x: x["market_cap"], reverse=True)
        
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
