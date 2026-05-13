"""
StockInsight Omni - 메인 앱
Cross-Platform AI Stock Analysis Hub
"""
import streamlit as st

# ─── 페이지 설정 (반드시 첫 번째 호출) ───
st.set_page_config(
    page_title="StockInsight Omni",
    page_icon="📊",
    layout="wide",
    initial_sidebar_state="expanded",
    menu_items={
        "About": "StockInsight Omni - AI 기반 크로스플랫폼 주식 분석 허브",
    },
)

from styles import inject_custom_css, render_page_header, render_disclaimer
from config import (
    MARKET_INDICES, DEFAULT_WATCHLIST, PERIOD_OPTIONS,
    POPULAR_TICKERS, AI_MODELS, COLORS, BACKTEST_DEFAULTS,
    ASSET_NAME_TO_TICKER,
)

# ─── CSS 주입 ───
inject_custom_css()


# ══════════════════════════════════════════════
# 사이드바
# ══════════════════════════════════════════════
def render_sidebar():
    """사이드바 네비게이션 및 설정"""
    with st.sidebar:
        st.markdown("""
        <div style="text-align:center; padding: 1rem 0 0.5rem 0;">
            <span style="font-size: 2.2rem;">📊</span>
            <h2 style="margin: 0.3rem 0 0 0; font-size: 1.2rem; font-weight: 800;
                background: linear-gradient(135deg, #3861fb, #8b5cf6);
                -webkit-background-clip: text; -webkit-text-fill-color: transparent;">
                StockInsight Omni
            </h2>
            <p style="color: #545b73; font-size: 0.7rem; margin: 0.2rem 0 0 0;">
                AI-Powered Stock Analysis
            </p>
        </div>
        """, unsafe_allow_html=True)

        st.divider()

        page = st.radio(
            "NAVIGATION",
            ["📊 대시보드", "📈 기술적 분석", "🤖 AI 애널리스트",
             "🔮 AI 예측", "💼 백테스터", "⚙️ 설정"],
            label_visibility="collapsed",
        )

        st.divider()

        # 종목 검색
        st.markdown('<p style="font-size:0.7rem; color:#8b92a5; font-weight:600; letter-spacing:0.5px;">🔍 종목 검색</p>', unsafe_allow_html=True)
        ticker_input = st.text_input(
            "종목 코드 입력", value="", placeholder="예: AAPL, 005930.KS",
            label_visibility="collapsed",
        )

        # 프리미엄 AI 설정
        with st.expander("🔑 AI API 설정"):
            ai_provider = st.selectbox(
                "AI 서비스", ["없음 (무료 HF)", "GPT (OpenAI)", "Gemini (Google)"],
            )
            api_key = ""
            ai_model = None
            if ai_provider != "없음 (무료 HF)":
                api_key = st.text_input(
                    "API Key", type="password", placeholder="sk-... 또는 AI...",
                )
                if "GPT" in ai_provider:
                    ai_model = st.selectbox("모델", AI_MODELS["gpt"]["models"])
                elif "Gemini" in ai_provider:
                    ai_model = st.selectbox("모델", AI_MODELS["gemini"]["models"])

            st.session_state["ai_provider"] = ai_provider
            st.session_state["api_key"] = api_key
            st.session_state["ai_model"] = ai_model

        st.divider()
        render_disclaimer()

    return page, ticker_input


# ══════════════════════════════════════════════
# 페이지: 대시보드
# ══════════════════════════════════════════════
def page_dashboard():
    """메인 대시보드 페이지"""
    from data_fetcher import get_market_indices, get_watchlist_data, format_price
    from styles import render_live_indicator

    render_page_header(
        "📊 시장 대시보드",
        f'{render_live_indicator()} 주요 시장 지수 및 관심 종목 현황'
    )

    # 시장 지수 카드
    with st.spinner("시장 데이터 로딩 중..."):
        indices = get_market_indices()

    if indices:
        cols = st.columns(min(len(indices), 3))
        for i, (name, data) in enumerate(indices.items()):
            with cols[i % len(cols)]:
                delta_str = f"{data['change']:+,.2f} ({data['change_pct']:+.2f}%)"
                st.metric(
                    label=f"{data['flag']} {name}",
                    value=f"{data['current']:,.2f}",
                    delta=delta_str,
                )
    else:
        st.info("📡 시장 데이터를 불러오는 중입니다. 잠시만 기다려주세요.")

    st.divider()

    # 관심 종목
    st.subheader("⭐ 관심 종목")

    tab_labels = list(DEFAULT_WATCHLIST.keys())
    tabs = st.tabs(tab_labels)

    for tab, (group_name, tickers) in zip(tabs, DEFAULT_WATCHLIST.items()):
        with tab:
            with st.spinner(f"{group_name} 데이터 로딩..."):
                watchlist = get_watchlist_data(tickers)

            if watchlist:
                import pandas as pd
                df_display = pd.DataFrame(watchlist)
                df_display["등락률"] = df_display["change_pct"].apply(
                    lambda x: f"{'🟢' if x >= 0 else '🔴'} {x:+.2f}%"
                )
                df_display["거래량"] = df_display["volume"].apply(lambda x: f"{x:,.0f}")
                df_display = df_display.rename(columns={
                    "name": "종목명", "ticker": "티커", "price": "현재가",
                })

                display_cols = ["종목명", "티커", "현재가", "등락률", "거래량"]
                st.dataframe(
                    df_display[display_cols],
                    width="stretch",
                    hide_index=True,
                    height=min(400, len(df_display) * 40 + 50),
                )
            else:
                st.info("데이터를 불러올 수 없습니다.")


# ══════════════════════════════════════════════
# 페이지: 기술적 분석
# ══════════════════════════════════════════════
def page_technical(ticker_input: str):
    """기술적 분석 페이지"""
    from data_fetcher import get_stock_data, get_stock_info, format_number, format_price
    from indicators import (
        create_candlestick_chart, create_rsi_chart, create_macd_chart,
    )

    render_page_header("📈 기술적 분석", "캔들스틱 차트, 이동평균선, RSI, MACD 지표")

    # 종목 선택
    col1, col2, col3 = st.columns([2, 1, 1])
    with col1:
        ticker = st.text_input(
            "종목 코드", value=ticker_input or "AAPL",
            key="tech_ticker", placeholder="예: AAPL, MSFT, 005930.KS",
        )
    with col2:
        period_label = st.selectbox("기간", list(PERIOD_OPTIONS.keys()), index=3)
        period = PERIOD_OPTIONS[period_label]
    with col3:
        ma_options = st.multiselect(
            "이동평균선", [5, 10, 20, 60, 120], default=[5, 20, 60],
        )

    show_bb = st.checkbox("볼린저 밴드 표시", value=False)

    if ticker:
        with st.spinner(f"{ticker} 데이터 로딩 중..."):
            df = get_stock_data(ticker, period)
            info = get_stock_info(ticker)

        if df.empty:
            st.error(f"❌ {ticker}의 데이터를 찾을 수 없습니다. 종목 코드를 확인해주세요.")
            return

        # 종목 정보 카드
        if "error" not in info:
            cols = st.columns(4)
            with cols[0]:
                price = info.get("current_price")
                st.metric("현재가", format_price(price, info.get("currency", "USD")))
            with cols[1]:
                st.metric("시가총액", format_number(info.get("market_cap"), info.get("currency", "")))
            with cols[2]:
                per = info.get("per")
                st.metric("PER", f"{per:.2f}" if per else "N/A")
            with cols[3]:
                dy = info.get("dividend_yield")
                st.metric("배당수익률", f"{dy*100:.2f}%" if dy else "N/A")

        st.divider()

        # 캔들스틱 차트
        st.plotly_chart(
            create_candlestick_chart(df, ma_options, show_bb),
            width="stretch",
        )

        # RSI & MACD
        col_rsi, col_macd = st.columns(2)
        with col_rsi:
            st.plotly_chart(create_rsi_chart(df), width="stretch")
        with col_macd:
            st.plotly_chart(create_macd_chart(df), width="stretch")


# ══════════════════════════════════════════════
# 페이지: AI 애널리스트
# ══════════════════════════════════════════════
def page_ai_analyst(ticker_input: str):
    """AI 챗봇 & 심층 분석 페이지"""
    from ai_agent import get_ai_agent, format_financial_data_for_prompt
    from styles import render_badge

    render_page_header("🤖 AI 애널리스트", "AI 기반 주식 분석 & 챗봇")

    # AI 에이전트 설정
    provider = st.session_state.get("ai_provider", "없음 (무료 HF)")
    api_key = st.session_state.get("api_key", "")
    ai_model = st.session_state.get("ai_model")

    premium_provider = None
    if "GPT" in provider:
        premium_provider = "gpt"
    elif "Gemini" in provider:
        premium_provider = "gemini"

    agent, tier = get_ai_agent(premium_provider, api_key, ai_model)

    # 티어 표시
    if tier == "premium":
        st.markdown(render_badge("PREMIUM", "premium"), unsafe_allow_html=True)
    else:
        st.markdown(render_badge("FREE", "free"), unsafe_allow_html=True)
        st.caption("💡 사이드바에서 GPT/Gemini API 키를 입력하면 심층 분석 기능이 활성화됩니다.")

    # 프리미엄 전용: 재무 분석 탭
    if tier == "premium":
        tab_chat, tab_analysis = st.tabs(["💬 챗봇", "📊 재무 분석"])
    else:
        tab_chat = st.container()
        tab_analysis = None

    # 챗봇 탭
    with tab_chat:
        # 세션 초기화
        if "ai_messages" not in st.session_state:
            st.session_state.ai_messages = []

        # 대화 이력 표시
        for msg in st.session_state.ai_messages:
            with st.chat_message(msg["role"]):
                st.markdown(msg["content"])

        # 입력
        if prompt := st.chat_input("주식에 대해 무엇이든 물어보세요..."):
            st.session_state.ai_messages.append({"role": "user", "content": prompt})
            with st.chat_message("user"):
                st.markdown(prompt)

            with st.chat_message("assistant"):
                response = st.write_stream(
                    agent.chat(st.session_state.ai_messages)
                )
            st.session_state.ai_messages.append({"role": "assistant", "content": response})

    # 재무 분석 탭 (프리미엄)
    if tab_analysis is not None:
        with tab_analysis:
            from data_fetcher import get_stock_info, get_financial_statements

            analysis_ticker = st.text_input(
                "분석할 종목", value=ticker_input or "AAPL",
                key="analysis_ticker",
            )
            if st.button("🔍 AI 재무 분석 시작", key="btn_analysis"):
                with st.spinner("재무 데이터 수집 중..."):
                    info = get_stock_info(analysis_ticker)
                    financials = get_financial_statements(analysis_ticker)

                if "error" in info:
                    st.error(f"❌ {analysis_ticker} 데이터를 찾을 수 없습니다.")
                else:
                    data_text = format_financial_data_for_prompt(info, financials)
                    st.markdown("---")
                    st.subheader(f"📊 {info.get('name', analysis_ticker)} AI 분석 리포트")
                    response = st.write_stream(agent.analyze_financials(data_text))


# ══════════════════════════════════════════════
# 페이지: AI 예측
# ══════════════════════════════════════════════
def page_ai_prediction(ticker_input: str):
    """Prophet 기반 AI 예측 페이지"""
    from predictor import StockPredictor

    render_page_header("🔮 AI 주가 예측", "Prophet 모델 기반 과거 패턴 분석 및 미래 예측")

    col1, col2, col3 = st.columns([2, 1, 1])
    with col1:
        ticker = st.text_input(
            "예측할 종목", value=ticker_input or "AAPL",
            key="pred_ticker",
        )
    with col2:
        data_period = st.selectbox("학습 데이터 기간", ["2y", "5y", "max"], index=1)
    with col3:
        forecast_days = st.slider("예측 일수", 30, 365, 90)

    if st.button("🔮 예측 시작", key="btn_predict"):
        predictor = StockPredictor()

        with st.spinner("Prophet 모델 학습 중... (최초 실행 시 시간이 걸릴 수 있습니다)"):
            success = predictor.predict(ticker, data_period, forecast_days)

        if not success:
            st.error(f"❌ {ticker} 예측 실패. 종목 코드와 데이터 기간을 확인해주세요.")
            return

        # 투자 매력도 & 기대 수익률
        col_gauge, col_returns = st.columns(2)
        with col_gauge:
            st.plotly_chart(predictor.create_gauge_chart(), width="stretch")
        with col_returns:
            st.plotly_chart(predictor.create_return_range_chart(), width="stretch")

        # 기대 수익률 상세
        ret = predictor.get_expected_return_range()
        if ret:
            st.divider()
            cols = st.columns(4)
            with cols[0]:
                st.metric("현재가", f"${ret['current_price']:,.2f}")
            with cols[1]:
                st.metric("예측가", f"${ret['expected_price']:,.2f}")
            with cols[2]:
                st.metric("기대 수익률", f"{ret['expected_return']:+.1f}%")
            with cols[3]:
                spread = ret['best_case_return'] - ret['worst_case_return']
                st.metric("변동 범위", f"{spread:.1f}%p")

        st.divider()

        # 예측 차트
        st.subheader("📉 주가 예측 차트")
        st.plotly_chart(predictor.create_forecast_chart(), width="stretch")

        # 면책 조항
        st.markdown("""
        <div class="disclaimer">
            🔬 <strong>참고:</strong> Prophet 예측은 과거 가격 패턴에 기반한 통계 모델입니다.
            실제 주가는 뉴스, 경제 상황, 시장 심리 등 다양한 요인에 영향을 받으며,
            본 예측은 투자 조언이 아닙니다. 모든 투자 결정은 본인 판단 하에 이루어져야 합니다.
        </div>
        """, unsafe_allow_html=True)


# ══════════════════════════════════════════════
# 페이지: 백테스터
# ══════════════════════════════════════════════
def page_backtester():
    """포트폴리오 백테스트 페이지"""
    from backtester import PortfolioBacktester
    from datetime import datetime, timedelta

    render_page_header("💼 포트폴리오 백테스터", "과거 데이터 기반 포트폴리오 성과 시뮬레이션")

    # 세션 상태 초기화 (동적 자산 리스트 및 선택 항목 보전)
    if "bt_asset_map" not in st.session_state:
        st.session_state.bt_asset_map = ASSET_NAME_TO_TICKER.copy()
    if "bt_selected_assets" not in st.session_state:
        st.session_state.bt_selected_assets = ["애플 (Apple - AAPL)", "마이크로소프트 (Microsoft - MSFT)", "구글 (Alphabet - GOOGL)"]

    # 포트폴리오 구성 UI
    st.subheader("📋 포트폴리오 구성")

    col_select, col_add = st.columns([3, 1])
    with col_select:
        # 다중 선택 (세션 상태 연동으로 실시간 추가 지원)
        selected_assets = st.multiselect(
            "📊 포트폴리오 종목 선택 (기업명으로 검색 가능)",
            options=list(st.session_state.bt_asset_map.keys()),
            key="bt_selected_assets",
            help="원하는 기업명이나 티커를 검색해 보세요. 여러 개를 중복하여 고를 수 있습니다."
        )

    with col_add:
        # 실시간 글로벌 종목 검색 팝오버
        with st.popover("🔍 기업명 검색 및 추가", width="stretch"):
            st.markdown("##### 💡 티커를 모르신다면 검색하세요!")
            st.caption("기업명 영문 사명, 혹은 티커 숫자를 입력해 실시간 데이터를 검색합니다.")
            
            search_q = st.text_input(
                "주소록/기업 검색창", 
                placeholder="예: Tesla, Samsung, Kakao, 005930",
                key="bt_ticker_search_q",
                label_visibility="collapsed"
            )
            
            if search_q:
                import yfinance as yf
                try:
                    with st.spinner("마켓 데이터 조회 중..."):
                        search_res = yf.Search(search_q.strip(), max_results=6)
                    
                    if search_res and search_res.quotes:
                        st.markdown("**📋 검색 매칭 결과 (클릭 시 즉시 포트폴리오 등록):**")
                        for quote in search_res.quotes:
                            symbol = quote.get("symbol")
                            raw_name = quote.get("shortname") or quote.get("longname") or "이름없음"
                            ex = quote.get("exchange", "N/A")
                            
                            # 표시 가독성을 위해 적절한 문자열 압축
                            disp_name = raw_name[:15] + ".." if len(raw_name) > 17 else raw_name
                            btn_label = f"➕ [{ex}] {symbol} | {disp_name}"
                            
                            # 버튼 액션: 맵에 넣고, 세션 선택 리스트에 병합 후 새로고침
                            if st.button(btn_label, key=f"s_btn_{symbol}", width="stretch"):
                                formatted_name = f"{raw_name} ({symbol})"
                                
                                # 리스트 맵에 등록
                                if formatted_name not in st.session_state.bt_asset_map:
                                    st.session_state.bt_asset_map[formatted_name] = symbol
                                
                                # 선택 목록에 강제 추가
                                if formatted_name not in st.session_state.bt_selected_assets:
                                    st.session_state.bt_selected_assets.append(formatted_name)
                                
                                st.toast(f"✅ {symbol} ({disp_name}) 종목을 포트폴리오에 바로 추가했습니다!")
                                st.rerun()
                    else:
                        st.warning("🔍 매칭되는 종목을 찾지 못했습니다. 영문명을 정확히 써보세요.")
                except Exception as e:
                    st.error(f"⚠️ 검색 시스템 오류: {str(e)}")
            
            st.divider()
            st.caption("💡 **검색 꿀팁**: 한글 종목은 `Samsung`, `Hyundai`, `Kakao`, `Naver` 같은 영문 발음이나 `005930` 처럼 종목번호 숫자로 검색하시면 가장 정확합니다.")

    # 종목 및 비중 데이터 구성
    tickers = []
    weights = []

    if selected_assets:
        st.markdown('<p style="font-weight: 600; font-size: 0.95rem; margin-top: 10px; margin-bottom: 5px;">⚖️ 종목별 투자 비중 (%)</p>', unsafe_allow_html=True)
        
        # 3열 그리드로 보기 좋게 나열
        grid_cols = st.columns(min(len(selected_assets), 3))
        total_entered_pct = 0
        
        # 기본으로 균등 비중 부여
        base_val = int(100 / len(selected_assets))

        for i, asset in enumerate(selected_assets):
            col_idx = i % 3
            with grid_cols[col_idx]:
                ticker = st.session_state.bt_asset_map[asset]
                tickers.append(ticker)
                
                # 기업명 깔끔하게 파싱해 표시 (괄호 전까지만)
                clean_name = asset.split("(")[0].strip()
                
                # 개별 비중 입력 위젯
                pct = st.number_input(
                    f"{clean_name} ({ticker})",
                    min_value=1, max_value=100,
                    value=base_val,
                    step=5,
                    key=f"bt_pct_{ticker}_{i}"
                )
                weights.append(float(pct))
                total_entered_pct += pct

        # 합계 알림 가이드
        if total_entered_pct != 100:
            st.info(f"💡 현재 입력 합계: **{total_entered_pct}%** (비율대로 100% 정규화되어 자동 연산됩니다.)")
        else:
            st.success(f"✅ 비중 합계가 정확히 **100%** 입니다!")
    else:
        st.warning("위의 선택창에서 분석하고자 하는 종목을 한 개 이상 지정해 주세요.")
        return

    st.divider()

    # 시뮬레이션 기간 및 기타 설정
    st.subheader("⚙️ 기간 및 초기 자산")
    col3, col4, col5 = st.columns(3)
    with col3:
        start_date = st.date_input(
            "시작일", value=datetime.now() - timedelta(days=3*365),
        )
    with col4:
        end_date = st.date_input("종료일", value=datetime.now())
    with col5:
        initial_capital = st.number_input(
            "초기 투자금 (KRW/USD)",
            value=BACKTEST_DEFAULTS["initial_capital"],
            step=1_000_000,
            format="%d",
        )

    benchmark = st.selectbox(
        "비교 기준 벤치마크", ["SPY (S&P 500)", "QQQ (NASDAQ)", "EWY (한국)"],
    )
    benchmark_ticker = benchmark.split(" ")[0]

    if st.button("🚀 포트폴리오 백테스트 가동", key="btn_backtest"):
        if len(tickers) == 0:
            st.error("❌ 분석할 종목이 지정되지 않았습니다.")
            return

        bt = PortfolioBacktester()
        bt.set_portfolio(
            tickers, weights,
            str(start_date), str(end_date),
            initial_capital,
        )

        with st.spinner("백테스트 실행 중..."):
            success = bt.run_backtest()

        if not success:
            st.error("❌ 백테스트 실패. 종목 코드와 기간을 확인해주세요.")
            return

        # 벤치마크 비교
        bt.compare_benchmark(benchmark_ticker)

        # 핵심 지표
        st.divider()
        st.subheader("📊 성과 지표")
        m = bt.metrics
        cols = st.columns(4)
        with cols[0]:
            st.metric("총 수익률", f"{m['total_return']*100:+.2f}%")
        with cols[1]:
            st.metric("연평균 수익률 (CAGR)", f"{m['cagr']*100:+.2f}%")
        with cols[2]:
            st.metric("최대 낙폭 (MDD)", f"{m['mdd']*100:.2f}%")
        with cols[3]:
            st.metric("샤프 지수", f"{m['sharpe']:.2f}")

        cols2 = st.columns(4)
        with cols2[0]:
            st.metric("변동성", f"{m['volatility']*100:.1f}%")
        with cols2[1]:
            st.metric("소르티노", f"{m['sortino']:.2f}")
        with cols2[2]:
            st.metric("투자 기간", f"{m['years']:.1f}년")
        with cols2[3]:
            final_val = bt.portfolio_value.iloc[-1] if bt.portfolio_value is not None else 0
            st.metric("최종 자산", f"₩{final_val:,.0f}")

        st.divider()

        # 누적 수익률 차트
        st.subheader("📈 누적 수익률")
        st.plotly_chart(bt.create_cumulative_chart(), width="stretch")

        # Drawdown & 히트맵
        col_dd, col_hm = st.columns(2)
        with col_dd:
            st.subheader("📉 Drawdown")
            st.plotly_chart(bt.create_drawdown_chart(), width="stretch")
        with col_hm:
            st.subheader("🗓️ 월별 수익률")
            st.plotly_chart(bt.create_monthly_heatmap(), width="stretch")


# ══════════════════════════════════════════════
# 페이지: 설정
# ══════════════════════════════════════════════
def page_settings():
    """설정 페이지"""
    render_page_header("⚙️ 설정", "API 키 관리 및 앱 정보")

    st.subheader("🔑 API 키 상태")
    provider = st.session_state.get("ai_provider", "없음")
    api_key = st.session_state.get("api_key", "")

    # Hugging Face 토큰 검출 안전 장치 (secrets.toml 부재 에러 방지)
    hf_active = False
    try:
        if "HF_TOKEN" in st.secrets and st.secrets["HF_TOKEN"]:
            hf_active = True
    except Exception:
        pass

    cols = st.columns(3)
    with cols[0]:
        hf_status = "✅ 설정됨" if hf_active else "❌ 미설정"
        st.metric("Hugging Face", hf_status)
    with cols[1]:
        gpt_status = "✅ 활성" if "GPT" in provider and api_key else "⬜ 비활성"
        st.metric("GPT (OpenAI)", gpt_status)
    with cols[2]:
        gem_status = "✅ 활성" if "Gemini" in provider and api_key else "⬜ 비활성"
        st.metric("Gemini (Google)", gem_status)

    st.divider()
    st.subheader("ℹ️ 앱 정보")
    st.markdown("""
    | 항목 | 정보 |
    |------|------|
    | **앱 이름** | StockInsight Omni |
    | **버전** | 1.0.0 |
    | **프레임워크** | Streamlit |
    | **데이터 소스** | Yahoo Finance (yfinance) |
    | **AI (무료)** | Hugging Face Inference API |
    | **AI (프리미엄)** | OpenAI GPT / Google Gemini |
    | **예측 모델** | Meta Prophet |
    """)

    st.divider()
    st.subheader("📱 아이폰 홈 화면 등록 방법")
    st.markdown("""
    1. **Safari**에서 이 앱의 URL에 접속합니다.
    2. 하단의 **공유 버튼** (□↑)을 탭합니다.
    3. **"홈 화면에 추가"**를 선택합니다.
    4. 이름을 확인하고 **"추가"**를 탭합니다.
    5. 홈 화면에서 앱 아이콘을 탭하면 전체 화면으로 실행됩니다! 🎉
    """)

    render_disclaimer()


# ══════════════════════════════════════════════
# 메인 실행
# ══════════════════════════════════════════════
def main():
    page, ticker_input = render_sidebar()

    if page == "📊 대시보드":
        page_dashboard()
    elif page == "📈 기술적 분석":
        page_technical(ticker_input)
    elif page == "🤖 AI 애널리스트":
        page_ai_analyst(ticker_input)
    elif page == "🔮 AI 예측":
        page_ai_prediction(ticker_input)
    elif page == "💼 백테스터":
        page_backtester()
    elif page == "⚙️ 설정":
        page_settings()


if __name__ == "__main__":
    main()
