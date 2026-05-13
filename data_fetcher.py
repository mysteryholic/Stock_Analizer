"""
StockInsight Omni - 데이터 수집 모듈
yfinance 기반 주식 데이터 수집, 캐싱, 에러 핸들링
"""
import streamlit as st
import yfinance as yf
import pandas as pd
import concurrent.futures
import FinanceDataReader as fdr
from datetime import datetime, timedelta
from config import MARKET_INDICES, INTERVAL_MAP


@st.cache_data(ttl=86400, show_spinner=False)
def get_unified_krx_db() -> pd.DataFrame:
    """국내 주식(KRX) 및 ETF 리스트를 병합하여 통합 로컬 탐색 데이터베이스 생성"""
    data = []
    
    # 1. 국내 정규 주식 로드
    try:
        df_krx = fdr.StockListing('KRX')
        if not df_krx.empty:
            for _, row in df_krx.iterrows():
                mkt = str(row.get('Market', 'KOSPI')).upper()
                suffix = ".KS" if mkt == "KOSPI" else ".KQ"
                data.append({
                    "symbol": f"{row['Code']}{suffix}",
                    "name": str(row['Name']),
                    "exchange": mkt
                })
    except Exception:
        pass
        
    # 2. 국내 ETF 로드 (Yahoo 등 글로벌 검색에서 누락되기 쉬운 ETF 보완)
    try:
        df_etf = fdr.StockListing('ETF/KR')
        if not df_etf.empty:
            for _, row in df_etf.iterrows():
                # 한국 ETF는 기본적으로 유가증권시장 상장 형식이므로 .KS suffix 부여
                data.append({
                    "symbol": f"{row['Symbol']}.KS",
                    "name": str(row['Name']),
                    "exchange": "ETF/KRX"
                })
    except Exception:
        pass
        
    return pd.DataFrame(data)


def expand_financial_keywords(query: str) -> list:
    """영문 금융 약어나 키워드를 한글로 교차 매핑하여 확장 키워드셋 생성"""
    translation_map = {
        "US": "미국", "USA": "미국",
        "TECH": "테크",
        "NASDAQ": "나스닥",
        "BOND": "채권",
        "DIVIDEND": "배당",
        "SEMICONDUCTOR": "반도체",
        "JAPAN": "일본",
        "CHINA": "중국",
        "GLOBAL": "글로벌",
        "INVERSE": "인버스",
        "LEVERAGE": "레버리지",
        "ACTIVE": "액티브",
        "TOTAL": "토탈",
        "RETURN": "리턴",
    }
    
    tokens = query.strip().upper().split()
    expanded = []
    for t in tokens:
        expanded.append(t)
        if t in translation_map:
            expanded.append(translation_map[t])
    return expanded


@st.cache_data(ttl=300, show_spinner=False)
def unified_search(query: str, max_results: int = 5) -> list:
    """한국어/영어 교차 키워드 매칭 및 yfinance 글로벌 검색 통합 스마트 검색 엔진"""
    if not query:
        return []
    
    q = query.strip()
    results = []
    seen = set()
    
    # 1. [국내 주식/ETF 시장] 스마트 다중 키워드 관련도(Relevance Score) 기반 탐색
    try:
        df_db = get_unified_krx_db()
        if not df_db.empty:
            tokens = expand_financial_keywords(q)
            
            # 관련도 점수(Relevance Score) 계산
            def compute_match_score(row):
                row_name = str(row['name']).upper()
                row_symbol = str(row['symbol']).split('.')[0]
                
                score = 0
                # 티커 번호와 완벽하게 포함/일치할 경우 최고 가중치 부과
                if q.upper() in row_symbol:
                    score += 100
                
                # 키워드 매칭 점수 가산
                for token in tokens:
                    if token in row_name:
                        score += 1
                return score
                
            df_db['score'] = df_db.apply(compute_match_score, axis=1)
            
            # 1점 이상 획득한 항목을 점수 기준 내림차순으로 필터링
            matches = df_db[df_db['score'] > 0].sort_values(by='score', ascending=False).head(max_results)
            
            for _, row in matches.iterrows():
                sym = row['symbol']
                results.append({
                    "symbol": sym,
                    "name": row['name'],
                    "exchange": row['exchange']
                })
                seen.add(sym.upper())
    except Exception:
        pass

    # 2. [글로벌 시장] yfinance Search API 보완 연동 (미국주식 등 해외자산)
    try:
        res = yf.Search(q, max_results=max_results)
        if res and res.quotes:
            for quote in res.quotes:
                sym = quote.get("symbol", "").upper()
                if not sym or sym in seen:
                    continue
                
                name = quote.get("shortname") or quote.get("longname") or sym
                ex = quote.get("exchange", "N/A")
                
                results.append({
                    "symbol": sym,
                    "name": name,
                    "exchange": ex
                })
                seen.add(sym)
    except Exception:
        pass
        
    return results



@st.cache_data(ttl=86400, show_spinner=False)
def resolve_korean_ticker(ticker: str) -> str:
    """한국 6자리 숫자 티커를 감지하여 .KS 또는 .KQ 접미사를 동적으로 부여하는 폴백 로직"""
    if not ticker:
        return ticker
    t = ticker.strip().upper()
    # 6자리 숫자로 구성되었는지 검사 (코스피/코스닥)
    if t.isdigit() and len(t) == 6:
        ks_ticker = f"{t}.KS"
        try:
            # 최소 단위 기간 조회를 통한 데이터 실존 여부 초고속 검증
            test_stock = yf.Ticker(ks_ticker)
            test_df = test_stock.history(period="1d")
            if not test_df.empty:
                return ks_ticker
        except Exception:
            pass
        
        # 코스피 데이터가 없거나 에러 발생 시 코스닥 티커 리턴
        return f"{t}.KQ"
    return t


@st.cache_data(ttl=300, show_spinner=False)
def get_stock_data(ticker: str, period: str = "1y") -> pd.DataFrame:
    """주식 히스토리컬 데이터 수집 (5분 캐싱)"""
    try:
        ticker = resolve_korean_ticker(ticker)
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
def get_market_indices_v2() -> dict:
    """주요 시장 지수 현재 데이터 초고속 수집 + NaN 결측 방지벽 (2분 캐싱)"""
    results = {}
    tickers = [info["ticker"] for info in MARKET_INDICES.values()]
    
    try:
        # 1. 모든 지수를 단 한 번의 병렬 배치 쿼리로 고속 수집 (레이트리밋 완벽 우회)
        df = yf.download(tickers, period="5d", group_by='ticker', auto_adjust=True, progress=False)
        
        for name, info in MARKET_INDICES.items():
            try:
                sym = info["ticker"]
                if sym not in df.columns.get_level_values(0):
                    continue
                
                # 시간대 불일치 및 휴장 등으로 인한 빈 슬롯(NaN) 결측 행 전면 차단
                idx_df = df[sym].dropna(subset=["Close"])
                if idx_df.empty or len(idx_df) < 2:
                    continue
                
                current = float(idx_df["Close"].iloc[-1])
                previous = float(idx_df["Close"].iloc[-2])
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
    except Exception:
        pass
        
    return results


@st.cache_data(ttl=300, show_spinner=False)
def get_stock_info(ticker: str) -> dict:
    """기업 기본 정보 수집"""
    try:
        ticker = resolve_korean_ticker(ticker)
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
        ticker = resolve_korean_ticker(ticker)
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
def get_watchlist_data_v2(tickers: list) -> list:
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
