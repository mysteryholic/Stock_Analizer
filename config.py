"""
StockInsight - 전역 설정 모듈
글로벌 상수, 종목 리스트, 색상 팔레트, 기간 옵션 등 정의
"""

# ──────────────────────────────────────────────
# 시장 지수 티커
# ──────────────────────────────────────────────
MARKET_INDICES = {
    "KOSPI": {"ticker": "^KS11", "name": "코스피", "flag": "🇰🇷"},
    "S&P 500": {"ticker": "^GSPC", "name": "S&P 500", "flag": "🇺🇸"},
    "NASDAQ": {"ticker": "^IXIC", "name": "나스닥", "flag": "🇺🇸"},
    "DOW": {"ticker": "^DJI", "name": "다우존스", "flag": "🇺🇸"},
    "KOSDAQ": {"ticker": "^KQ11", "name": "코스닥", "flag": "🇰🇷"},
    "Nikkei 225": {"ticker": "^N225", "name": "닛케이", "flag": "🇯🇵"},
}

# ──────────────────────────────────────────────
# 기본 관심 종목 리스트
# ──────────────────────────────────────────────
DEFAULT_WATCHLIST = {
    "한국 대표": [
        {"ticker": "005930.KS", "name": "삼성전자"},
        {"ticker": "000660.KS", "name": "SK하이닉스"},
        {"ticker": "373220.KS", "name": "LG에너지솔루션"},
        {"ticker": "035420.KS", "name": "NAVER"},
        {"ticker": "035720.KS", "name": "카카오"},
    ],
    "미국 대표": [
        {"ticker": "AAPL", "name": "Apple"},
        {"ticker": "MSFT", "name": "Microsoft"},
        {"ticker": "NVDA", "name": "NVIDIA"},
        {"ticker": "TSLA", "name": "Tesla"},
        {"ticker": "GOOGL", "name": "Alphabet"},
        {"ticker": "AMZN", "name": "Amazon"},
    ],
}

# ──────────────────────────────────────────────
# 기간 옵션
# ──────────────────────────────────────────────
PERIOD_OPTIONS = {
    "1개월": "1mo",
    "3개월": "3mo",
    "6개월": "6mo",
    "1년": "1y",
    "2년": "2y",
    "5년": "5y",
    "최대": "max",
}

INTERVAL_MAP = {
    "1mo": "1d",
    "3mo": "1d",
    "6mo": "1d",
    "1y": "1d",
    "2y": "1wk",
    "5y": "1wk",
    "max": "1mo",
}

# ──────────────────────────────────────────────
# 색상 팔레트 (차트 & UI)
# ──────────────────────────────────────────────
COLORS = {
    # 메인 배경
    "bg_primary": "#0a0e27",
    "bg_secondary": "#121638",
    "bg_card": "rgba(18, 22, 56, 0.85)",
    "bg_card_hover": "rgba(26, 31, 72, 0.95)",

    # 강조 색상
    "accent_gold": "#f0b90b",
    "accent_blue": "#3861fb",
    "accent_purple": "#8b5cf6",

    # 상승/하락
    "bullish": "#00d4aa",
    "bearish": "#ff4757",

    # 텍스트
    "text_primary": "#e8eaed",
    "text_secondary": "#8b92a5",
    "text_muted": "#545b73",

    # 차트 색상
    "chart_line_1": "#3861fb",
    "chart_line_2": "#f0b90b",
    "chart_line_3": "#8b5cf6",
    "chart_line_4": "#00d4aa",
    "chart_line_5": "#ff6b6b",
    "chart_candle_up": "#00d4aa",
    "chart_candle_down": "#ff4757",
    "chart_volume": "rgba(56, 97, 251, 0.4)",

    # 그라데이션
    "gradient_start": "#3861fb",
    "gradient_end": "#8b5cf6",
}

# ──────────────────────────────────────────────
# AI 모델 설정
# ──────────────────────────────────────────────
AI_MODELS = {
    "huggingface": {
        "model_id": "Qwen/Qwen2.5-7B-Instruct",
        "display_name": "🆓 AI 어시스턴트 (무료)",
    },
    "gpt": {
        "models": ["gpt-5", "gpt-4o", "gpt-4o-mini", "gpt-4-turbo", "직접 입력 (Custom)"],
        "display_name": "⭐ GPT (프리미엄)",
    },
    "gemini": {
        "models": [
            "gemini-2.5-flash", "gemini-2.5-pro", 
            "gemini-1.5-flash", "gemini-1.5-pro",
            "gemini-3.1-flash", "직접 입력 (Custom)"
        ],
        "display_name": "⭐ Gemini (프리미엄)",
    },
}

# ──────────────────────────────────────────────
# 시스템 프롬프트
# ──────────────────────────────────────────────
STOCK_SYSTEM_PROMPT = """당신은 'StockInsight AI'라는 이름의 전문 주식 분석 어시스턴트입니다.

역할:
- 주식 시장 분석, 기업 재무 분석, 투자 전략에 대해 전문적으로 답변합니다.
- 한국어로 친절하고 명확하게 답변합니다.
- 기술적 분석(차트 패턴, 지표)과 기본적 분석(재무제표, 밸류에이션) 모두 다룹니다.

주의사항:
- 투자 권유가 아닌 정보 제공 목적임을 항상 명시합니다.
- 확실하지 않은 정보는 추측임을 밝힙니다.
- 리스크 관리의 중요성을 강조합니다.
"""

FINANCIAL_ANALYSIS_PROMPT = """다음 재무 데이터를 분석하여 투자자에게 유용한 인사이트를 제공해주세요.

{financial_data}

다음 형식으로 답변해주세요:
1. **📊 핵심 재무 지표 분석**: 매출, 영업이익, 순이익 트렌드
2. **💰 밸류에이션 평가**: PER, PBR 등 상대적 가치 평가
3. **⚠️ 리스크 요인**: 주의해야 할 사항
4. **🎯 종합 의견**: 전반적인 투자 매력도

마지막에 반드시 **초보자용 3줄 요약**을 이모지와 함께 제공해주세요.
"""

# ──────────────────────────────────────────────
# 포트폴리오 백테스트 기본 설정
# ──────────────────────────────────────────────
BACKTEST_DEFAULTS = {
    "initial_capital": 10_000_000,  # 1천만원
    "risk_free_rate": 0.035,       # 무위험 수익률 3.5%
    "benchmark_ticker": "SPY",     # 기본 벤치마크
}

# ──────────────────────────────────────────────
# 인기 종목 검색용 (빠른 선택)
# ──────────────────────────────────────────────
POPULAR_TICKERS = [
    "AAPL", "MSFT", "NVDA", "TSLA", "GOOGL", "AMZN", "META",
    "005930.KS", "000660.KS", "373220.KS", "035420.KS",
    "SPY", "QQQ", "ARKK",
]

# ──────────────────────────────────────────────
# 백테스터용 기업명 맵핑 사전
# ──────────────────────────────────────────────
ASSET_NAME_TO_TICKER = {
    "애플 (Apple - AAPL)": "AAPL",
    "마이크로소프트 (Microsoft - MSFT)": "MSFT",
    "엔비디아 (NVIDIA - NVDA)": "NVDA",
    "테슬라 (Tesla - TSLA)": "TSLA",
    "구글 (Alphabet - GOOGL)": "GOOGL",
    "아마존 (Amazon - AMZN)": "AMZN",
    "메타 (Meta - META)": "META",
    "삼성전자 (005930.KS)": "005930.KS",
    "SK하이닉스 (000660.KS)": "000660.KS",
    "LG에너지솔루션 (373220.KS)": "373220.KS",
    "네이버 (NAVER - 035420.KS)": "035420.KS",
    "카카오 (Kakao - 035720.KS)": "035720.KS",
    "SPY (S&P500 ETF)": "SPY",
    "QQQ (나스닥100 ETF)": "QQQ",
    "ARKK (혁신기술 ETF)": "ARKK",
}

