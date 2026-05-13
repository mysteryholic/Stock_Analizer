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
# 공용 컴포넌트
# ══════════════════════════════════════════════
import json, os

WATCHLIST_PATH = os.path.join(os.path.dirname(__file__), "watchlist.json")

def load_my_watchlist() -> list:
    """JSON 파일에서 관심 종목 리스트 로드"""
    try:
        if os.path.exists(WATCHLIST_PATH):
            with open(WATCHLIST_PATH, "r", encoding="utf-8") as f:
                return json.load(f)
    except Exception:
        pass
    return []

def save_my_watchlist(wl: list):
    """관심 종목 리스트를 JSON 파일에 저장"""
    try:
        with open(WATCHLIST_PATH, "w", encoding="utf-8") as f:
            json.dump(wl, f, ensure_ascii=False, indent=2)
    except Exception:
        pass

def init_watchlist_state():
    """세션 상태의 관심 종목 리스트를 초기화 (파일 우선)"""
    if "my_watchlist" not in st.session_state:
        st.session_state.my_watchlist = load_my_watchlist()

def add_to_watchlist(ticker: str, name: str = ""):
    init_watchlist_state()
    entry = {"ticker": ticker, "name": name or ticker}
    if not any(e["ticker"] == ticker for e in st.session_state.my_watchlist):
        st.session_state.my_watchlist.append(entry)
        save_my_watchlist(st.session_state.my_watchlist)

def remove_from_watchlist(ticker: str):
    init_watchlist_state()
    st.session_state.my_watchlist = [
        e for e in st.session_state.my_watchlist if e["ticker"] != ticker
    ]
    save_my_watchlist(st.session_state.my_watchlist)


def render_stock_selector(label: str, key_prefix: str, default_ticker: str = "AAPL") -> str:
    """실시간 글로벌 종목 검색창(엔터 지원)이 결합된 다기능 종목 선택 패널"""
    # 1. 세션 변수 초기화 (글로벌 공유 티커와 정적 매핑)
    session_key = f"ss_ticker_{key_prefix}"
    global_val = st.session_state.get("global_ticker", "")
    if session_key not in st.session_state:
        st.session_state[session_key] = global_val or default_ticker
    elif global_val and global_val != st.session_state[session_key]:
        st.session_state[session_key] = global_val

    # 2. 검색 리스트 임시 저장용 캐시 키 확보
    cache_key = f"res_cache_{key_prefix}"
    if cache_key not in st.session_state:
        st.session_state[cache_key] = None

    # 3. UI 폼 렌더링 (입력창 + 검색 버튼)
    with st.form(f"form_sel_{key_prefix}", border=False):
        col_inp, col_btn = st.columns([3, 1])
        with col_inp:
            query_val = st.text_input(
                label,
                value=st.session_state[session_key],
                placeholder="종목코드 직접 입력 또는 기업명 검색 (엔터키 지원)",
                key=f"f_inp_{key_prefix}"
            )
        with col_btn:
            st.markdown('<div style="height: 28px;" class="hide-mobile"></div>', unsafe_allow_html=True)
            submitted = st.form_submit_button("🔍 종목 조회", width="stretch")

    # 4. 제출 이벤트 처리 (엔터 클릭 또는 버튼 클릭)
    if submitted and query_val:
        from data_fetcher import unified_search
        q = query_val.strip()
        try:
            with st.spinner("정보 검색 중..."):
                res_list = unified_search(q, max_results=4)
            if res_list:
                top_sym = res_list[0]["symbol"].upper()
                # 사용자가 입력한 값이 첫 번째 검색 결과의 티커명과 완벽히 일치할 때 → 즉시 통과/선택
                if q.upper() == top_sym:
                    st.session_state[session_key] = top_sym
                    st.session_state["global_ticker"] = top_sym
                    st.session_state[cache_key] = None # 이전 검색 찌꺼기 소거
                    st.toast(f"✅ {top_sym} 종목이 활성화되었습니다!")
                    st.rerun()
                else:
                    # 사명 또는 유사어 검색일 때 → 추천 목록 화면 바인딩
                    st.session_state[cache_key] = res_list
            else:
                # 검색 불가 시 사용자가 입력한 값을 티커로 단독 밀어넣기 시도
                st.session_state[session_key] = q.upper()
                st.session_state["global_ticker"] = q.upper()
                st.session_state[cache_key] = None
                st.rerun()
        except Exception:
            # Yahoo API 타임아웃 등 발생 시 대체 통과
            st.session_state[session_key] = q
            st.session_state["global_ticker"] = q
            st.session_state[cache_key] = None
            st.rerun()

    # 5. 추천 검색 리스트 동적 팝아웃 생성
    if st.session_state[cache_key]:
        st.markdown("**💡 검색 추천 목록 (분석할 종목을 적용해 보세요):**")
        for item in st.session_state[cache_key]:
            sym = item["symbol"]
            nm = item["name"]
            ex = item["exchange"]
            
            r_c1, r_c2 = st.columns([3, 1])
            with r_c1:
                st.markdown(f"📊 **{nm}** &nbsp;&nbsp; `{sym}` &nbsp; <span style='color:#8b92a5; font-size:0.8rem;'>[{ex}]</span>", unsafe_allow_html=True)
            with r_c2:
                if st.button("📊 분석 적용", key=f"btn_apply_{key_prefix}_{sym}", width="stretch"):
                    st.session_state[session_key] = sym
                    st.session_state["global_ticker"] = sym
                    st.session_state[cache_key] = None # 선택 시 가시성 제거
                    st.toast(f"✅ {sym} ({nm}) 종목으로 분석을 가동합니다!")
                    st.rerun()
        st.divider()

    return st.session_state[session_key]


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

        # 종목 검색 (사이드바 — 글로벌 티커 설정)
        st.markdown('<p style="font-size:0.7rem; color:#8b92a5; font-weight:600; letter-spacing:0.5px;">🔍 종목 검색</p>', unsafe_allow_html=True)
        
        # 🛡️ 대시보드/외부 분석 적용 시, 사이드바 위젯 인스턴스화 직전에 세션 상태를 안전하게 동기화 (StreamlitAPIException 방어벽)
        g_tick = st.session_state.get("global_ticker", "")
        if g_tick and st.session_state.get("sidebar_ticker_input", "") != g_tick:
            st.session_state["sidebar_ticker_input"] = g_tick

        search_col, pop_col = st.columns([3, 1])
        with search_col:
            ticker_input = st.text_input(
                "종목 코드 입력", value=st.session_state.get("global_ticker", ""),
                placeholder="예: AAPL, 005930.KS",
                label_visibility="collapsed",
                key="sidebar_ticker_input",
            )
            if ticker_input:
                st.session_state["global_ticker"] = ticker_input.strip().upper()
        with pop_col:
            with st.popover("🔍", width="stretch"):
                st.caption("기업명으로 실시간 검색")
                sb_search = st.text_input(
                    "사이드바 검색",
                    placeholder="Tesla, Samsung…",
                    key="sb_search_q",
                    label_visibility="collapsed",
                )
                if sb_search:
                    from data_fetcher import unified_search
                    try:
                        with st.spinner("조회 중..."):
                            res_list = unified_search(sb_search.strip(), max_results=5)
                        if res_list:
                            for item in res_list:
                                sym = item["symbol"]
                                nm = item["name"][:12]
                                ex = item["exchange"]
                                btn_label = f"📊 {nm} ({sym}) [{ex}]"
                                if st.button(btn_label, key=f"sb_pop_{sym}", width="stretch"):
                                    st.session_state["global_ticker"] = sym
                                    st.toast(f"✅ {sym} 적용!")
                                    st.rerun()
                        else:
                            st.caption("결과 없음")
                    except Exception:
                        st.caption("검색 오류")
                st.caption("💡 Samsung, Kakao, 005930…")

        # 프리미엄 AI 설정
        with st.expander("🔑 AI API 설정"):
            # ─── 기본 서비스 자동 세팅 연산 (Secrets 기반) ───
            provider_opts = ["없음 (무료 HF)", "GPT (OpenAI)", "Gemini (Google)"]
            def_idx = 0
            
            if "ai_provider" in st.session_state:
                try: def_idx = provider_opts.index(st.session_state["ai_provider"])
                except: pass
            else:
                try:
                    if st.secrets.get("OPENAI_API_KEY"):
                        def_idx = 1
                    elif st.secrets.get("GEMINI_API_KEY"):
                        def_idx = 2
                except: pass

            ai_provider = st.selectbox("AI 서비스", provider_opts, index=def_idx)
            # ────── 기본 입력값 자동 링킹 (SessionState or Secrets) ──────
            def_hf = st.session_state.get("hf_token", "")
            if not def_hf:
                try: def_hf = st.secrets.get("HF_TOKEN", "")
                except: pass

            def_api = st.session_state.get("api_key", "")
            if not def_api:
                try:
                    if "GPT" in ai_provider: def_api = st.secrets.get("OPENAI_API_KEY", "")
                    elif "Gemini" in ai_provider: def_api = st.secrets.get("GEMINI_API_KEY", "")
                except: pass

            hf_token = ""
            api_key = ""
            ai_model = None
            
            if ai_provider == "없음 (무료 HF)":
                st.caption("🆓 최상급 오픈소스 한국어 AI(Qwen 2.5)를 가동합니다. 무상 발급받은 허깅페이스 토큰을 입력해 주세요.")
                hf_token = st.text_input(
                    "HF Access Token", type="password", placeholder="hf_...",
                    value=def_hf, key="ti_hf_sidebar"
                )
            else:
                api_key = st.text_input(
                    "API Key", type="password", placeholder="sk-... 또는 AI...",
                    value=def_api, key="ti_api_sidebar"
                )
                if "GPT" in ai_provider:
                    sel_model = st.selectbox("모델", AI_MODELS["gpt"]["models"])
                    if sel_model == "직접 입력 (Custom)":
                        ai_model = st.text_input("GPT 모델명 입력", placeholder="예: gpt-4.5-preview")
                    else:
                        ai_model = sel_model
                elif "Gemini" in ai_provider:
                    sel_model = st.selectbox("모델", AI_MODELS["gemini"]["models"])
                    if sel_model == "직접 입력 (Custom)":
                        ai_model = st.text_input("Gemini 모델명 입력", placeholder="예: gemini-2.5-pro")
                    else:
                        ai_model = sel_model

            st.session_state["ai_provider"] = ai_provider
            st.session_state["api_key"] = api_key
            st.session_state["ai_model"] = ai_model
            st.session_state["hf_token"] = hf_token

        st.divider()
        render_disclaimer()

    return page, st.session_state.get("global_ticker", ticker_input)


# ══════════════════════════════════════════════
# 페이지: 대시보드
# ══════════════════════════════════════════════
def page_dashboard():
    """메인 대시보드 페이지"""
    from data_fetcher import get_market_indices_v2, get_watchlist_data_v2, format_price
    from styles import render_live_indicator

    init_watchlist_state()

    render_page_header(
        "📊 시장 대시보드",
        f'{render_live_indicator()} 주요 시장 지수 및 관심 종목 현황'
    )

    # ── 종목 검색 바 (대시보드 전용) ──────────────────────
    st.markdown("##### 🔍 종목 검색")
    
    # 검색 결과 유지를 위한 세션 상태 관리
    if "dash_search_results" not in st.session_state:
        st.session_state.dash_search_results = None

    # st.form을 도입하여 '엔터키' 지원 + 레이아웃 자동 균형
    with st.form("dash_search_form", border=False):
        dash_col1, dash_col2 = st.columns([4, 1])
        with dash_col1:
            dash_search_q = st.text_input(
                "대시보드 검색", placeholder="기업명 또는 티커: Tesla, Samsung, AAPL… (엔터 가능)",
                label_visibility="collapsed", key="dash_search_q"
            )
        with dash_col2:
            submitted = st.form_submit_button("🔍 검색", width="stretch")

    # 폼이 제출되었을 때만 통합 검색 1회 실행 후 세션에 캐시
    if submitted and dash_search_q:
        from data_fetcher import unified_search
        try:
            with st.spinner("검색 중..."):
                res_list = unified_search(dash_search_q.strip(), max_results=5)
            if res_list:
                st.session_state.dash_search_results = res_list
            else:
                st.session_state.dash_search_results = []
                st.warning("🔍 검색 결과가 없습니다. 한글 기업명, 영문 사명, 혹은 티커 번호로 시도해보세요.")
        except Exception as e:
            st.error(f"⚠️ 검색 오류: {str(e)}")
            st.session_state.dash_search_results = None

    # 세션에 보관된 검색 결과를 렌더링 (관심 등록/해제 등의 재실행(rerun) 시에도 온전히 화면에 유지됨)
    if st.session_state.dash_search_results:
        st.markdown("**📋 검색 결과 — ⭐ 버튼으로 관심 등록 가능:**")
        for q in st.session_state.dash_search_results:
            sym = q["symbol"]
            nm = q["name"]
            ex = q["exchange"]
            in_wl = any(e["ticker"] == sym for e in st.session_state.my_watchlist)

            r1, r2, r3 = st.columns([3, 1, 1])
            with r1:
                st.markdown(f"📊 **{nm}** &nbsp;&nbsp; `{sym}` &nbsp; <span style='color:#8b92a5; font-size:0.8rem;'>[{ex}]</span>", unsafe_allow_html=True)
            with r2:
                if in_wl:
                    if st.button("❌ 해제", key=f"wl_remove_{sym}", width="stretch"):
                        remove_from_watchlist(sym)
                        st.toast(f"❌ {sym} 관심 해제 완료")
                        st.rerun()
                else:
                    if st.button("⭐ 등록", key=f"wl_add_{sym}", width="stretch"):
                        add_to_watchlist(sym, nm)
                        st.toast(f"⭐ {sym} 관심 등록 완료!")
                        st.rerun()
            with r3:
                if st.button("📈 분석", key=f"wl_go_{sym}", width="stretch"):
                    st.session_state["global_ticker"] = sym
                    st.toast(f"✅ {sym} 분석 페이지 연동!")
                    st.rerun()

    st.divider()

    # ── My Watchlist 섹션 ─────────────────────────────
    my_wl = st.session_state.my_watchlist
    if my_wl:
        st.markdown("#### ⭐ My Watchlist")
        with st.spinner("관심 종목 데이터 로딩..."):
            wl_data_map = {d["ticker"]: d for d in get_watchlist_data_v2(my_wl)}

        # 가로형 카드 레이아웃 (최대 4열)
        n_cols = min(len(my_wl), 4)
        wl_cols = st.columns(n_cols)
        for i, entry in enumerate(my_wl):
            sym = entry["ticker"]
            nm = entry.get("name", sym)
            d = wl_data_map.get(sym, {})
            price = d.get("price", 0)
            chg_pct = d.get("change_pct", 0)
            arrow = "🟢" if chg_pct >= 0 else "🔴"
            with wl_cols[i % n_cols]:
                st.markdown(
                    f"""
                    <div class="stock-card wl-card">
                        <div class="card-title">{sym}</div>
                        <div class="card-value">{f"{price:,.2f}" if price else "N/A"}</div>
                        <div class="card-delta {'delta-positive' if chg_pct >= 0 else 'delta-negative'}">
                            {arrow} {chg_pct:+.2f}%
                        </div>
                        <div style="font-size:0.65rem; color:#8b92a5; margin-top:4px;">{nm[:18]}</div>
                    </div>""",
                    unsafe_allow_html=True
                )
                if st.button("❌", key=f"wl_card_rm_{sym}", help=f"{sym} 관심 해제"):
                    remove_from_watchlist(sym)
                    st.rerun()

        st.divider()
    else:
        st.info("⭐ 관심 종목이 없습니다. 위 검색창에서 종목을 검색 후 등록해 보세요!")
        st.divider()

    # ── 시장 지수 카드 ─────────────────────────────────
    with st.spinner("시장 데이터 로딩 중..."):
        indices = get_market_indices_v2()

    if indices:
        cols = st.columns(min(len(indices), 4))
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

    # ── 프리셋 관심 종목 (탭) ──────────────────────────
    st.subheader("📋 시장별 종목 현황")

    tab_labels = list(DEFAULT_WATCHLIST.keys())
    tabs = st.tabs(tab_labels)

    for tab, (group_name, tickers) in zip(tabs, DEFAULT_WATCHLIST.items()):
        with tab:
            with st.spinner(f"{group_name} 데이터 로딩..."):
                watchlist = get_watchlist_data_v2(tickers)

            if watchlist:
                import pandas as pd
                from data_fetcher import format_number
                
                df_display = pd.DataFrame(watchlist)
                
                # 🛡️ 이전 구형 캐시 데이터 오염에 의한 KeyError 크래시 방지벽 가동
                if "market_cap" not in df_display.columns:
                    df_display["market_cap"] = 0
                if "currency" not in df_display.columns:
                    df_display["currency"] = ""
                    
                df_display["등락률"] = df_display["change_pct"].apply(
                    lambda x: f"{'🟢' if x >= 0 else '🔴'} {x:+.2f}%"
                )
                df_display["거래량"] = df_display["volume"].apply(lambda x: f"{x:,.0f}")
                
                # 국가별 통화 규격을 반영한 시가총액 시각적 변환 적용
                df_display["시가총액"] = df_display.apply(
                    lambda row: format_number(row["market_cap"], row["currency"]), axis=1
                )
                
                df_display = df_display.rename(columns={
                    "name": "종목명", "ticker": "티커", "price": "현재가",
                })

                # 시가총액 칼럼 추가 및 배치 
                display_cols = ["종목명", "티커", "현재가", "등락률", "시가총액", "거래량"]
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

    # 종목 선택기
    ticker = render_stock_selector("📊 분석할 종목 선택", "tech", default_ticker=ticker_input or "AAPL")

    col2, col3 = st.columns(2)
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
            st.error("⚠️ 지원하지 않는 종목이거나 티커를 확인해주세요.")
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
                # yfinance의 dividend_yield는 이미 퍼센트 단위 수치(예: 2.5)로 전달됩니다.
                st.metric("배당수익률", f"{dy:.2f}%" if dy else "N/A")

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
        
        # 라이브러리 로드 에러 검출 및 렌더링
        init_err = st.session_state.get("ai_init_error")
        if init_err:
            st.error(f"⚠️ **프리미엄 AI 활성화 오류 감지**\n\n`{init_err}`")
            st.warning("💡 **해결 안내:**\n"
                       "1. `google-genai` 등 최근 업데이트된 패키지가 서버(웹 사이트) 환경에 아직 설치되지 않았을 확률이 99%입니다.\n"
                       "2. 로컬의 최신 `requirements.txt` 파일을 배포 서버에 **Git Commit & Push**해 주신 후, **앱을 Reboot(재부팅)**하시면 즉시 해결됩니다!")
        else:
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

            analysis_ticker = render_stock_selector("📊 분석할 종목 선택", "analysis", default_ticker=ticker_input or "AAPL")
            if st.button("🤖 AI 심층 재무 분석 시작", key="btn_analysis", width="stretch"):
                with st.spinner("재무 데이터 수집 중..."):
                    info = get_stock_info(analysis_ticker)
                    financials = get_financial_statements(analysis_ticker)

                if "error" in info:
                    st.error("⚠️ 지원하지 않는 종목이거나 티커를 확인해주세요.")
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

    # 종목 선택기
    ticker = render_stock_selector("📊 예측할 종목 선택", "pred", default_ticker=ticker_input or "AAPL")

    col2, col3 = st.columns(2)
    with col2:
        data_period = st.selectbox("학습 데이터 기간", ["2y", "5y", "max"], index=1)
    with col3:
        forecast_days = st.slider("예측 일수", 30, 365, 90)

    if st.button("🔮 예측 시작", key="btn_predict"):
        predictor = StockPredictor()

        with st.spinner("Prophet 모델 학습 중... (최초 실행 시 시간이 걸릴 수 있습니다)"):
            success = predictor.predict(ticker, data_period, forecast_days)

        if not success:
            st.error("⚠️ 지원하지 않는 종목이거나 티커를 확인해주세요.")
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
                q_upper = search_q.strip().upper()
                # 💡 직접 입력 수동 반영 가이드 (6자리 숫자 코스피/코스닥 판정 엔진 포함)
                from data_fetcher import resolve_korean_ticker
                resolved_input = resolve_korean_ticker(q_upper)
                
                if st.button(f"➕ '{resolved_input}' 직접 포트폴리오 등록", key=f"s_direct_{q_upper}", width="stretch"):
                    formatted_name = f"{resolved_input} (직접 추가)"
                    if formatted_name not in st.session_state.bt_asset_map:
                        st.session_state.bt_asset_map[formatted_name] = resolved_input
                    if formatted_name not in st.session_state.bt_selected_assets:
                        st.session_state.bt_selected_assets.append(formatted_name)
                    st.toast(f"✅ {resolved_input} 추가 성공!")
                    st.rerun()
                
                st.markdown("<hr style='margin: 0.8rem 0;'/>", unsafe_allow_html=True)

                from data_fetcher import unified_search
                try:
                    with st.spinner("마켓 데이터 조회 중..."):
                        res_list = unified_search(search_q.strip(), max_results=6)
                    
                    if res_list:
                        st.markdown("**📋 검색 매칭 결과 (클릭 시 즉시 포트폴리오 등록):**")
                        for item in res_list:
                            symbol = item["symbol"]
                            raw_name = item["name"]
                            ex = item["exchange"]
                            
                            # 표시 가독성을 위해 적절한 문자열 압축
                            disp_name = raw_name[:14] + ".." if len(raw_name) > 16 else raw_name
                            btn_label = f"➕ {disp_name} ({symbol}) [{ex}]"
                            
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

    # 💵 현금 비중 설정
    st.markdown('<p style="font-weight: 600; font-size: 0.95rem; margin-top: 15px; margin-bottom: 5px;">💵 포트폴리오 현금(Cash) 비중 (%)</p>', unsafe_allow_html=True)
    cash_pct = st.slider(
        "현금을 보유하면 남은 비중이 주식 자산군으로 자동 정규화 배정되어 변동성을 완화합니다.", 
        min_value=0, max_value=100, value=0, step=5, format="%d%%",
        key="bt_cash_slider"
    )
    
    if cash_pct > 0:
        st.caption(f"💡 현재 구성: **현금 {cash_pct}%** + **주식 자산군 {100-cash_pct}%** 배정")

    # 종목 및 비중 데이터 구성
    tickers = []
    weights = []

    if selected_assets:
        st.markdown('<p style="font-weight: 600; font-size: 0.95rem; margin-top: 10px; margin-bottom: 5px;">⚖️ 주식 자산군 내 상대적 투자 비중 (%)</p>', unsafe_allow_html=True)
        
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
                
                # 기업명 깔끔하게 파싱해 표시
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
        if total_entered_pct > 0:
            st.success(f"✅ 주식 자산 {len(selected_assets)}개 비중 설정 완료! (입력 합계: {total_entered_pct}%)")
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
            cash_weight=(cash_pct / 100.0),
        )

        with st.spinner("백테스트 실행 중..."):
            success = bt.run_backtest()

        if not success:
            st.error("❌ 백테스트 실패. 종목 코드와 기간을 확인해주세요.")
            return

        # 벤치마크 비교
        bt.compare_benchmark(benchmark_ticker)

        # 핵심 지표 및 자산 배분
        st.divider()
        
        col_alloc, col_metrics = st.columns([1.0, 3.0], gap="medium")
        
        with col_alloc:
            st.markdown('<p style="font-weight: 600; font-size: 1.05rem; margin-bottom: 10px;">💼 최종 자산 구성</p>', unsafe_allow_html=True)
            import plotly.express as px
            alloc_df = bt.get_allocation_data()
            
            # 프리미엄 룩 다크 테마 도넛 차트
            fig_pie = px.pie(
                alloc_df, names="자산", values="비중 (%)", hole=0.45,
                color_discrete_sequence=["#3b82f6", "#60a5fa", "#93c5fd", "#2563eb", "#f59e0b", "#10b981"]
            )
            fig_pie.update_traces(
                textposition='inside', 
                textinfo='percent+label',
                textfont=dict(color='white', size=10),
                hoverinfo='label+percent'
            )
            fig_pie.update_layout(
                template="plotly_dark",
                paper_bgcolor="rgba(0,0,0,0)",
                plot_bgcolor="rgba(0,0,0,0)",
                margin=dict(l=5, r=5, t=5, b=5),
                height=240,
                showlegend=False
            )
            st.plotly_chart(fig_pie, width="stretch")
            
        with col_metrics:
            st.markdown('<p style="font-weight: 600; font-size: 1.05rem; margin-bottom: 10px;">📊 핵심 성과 지표</p>', unsafe_allow_html=True)
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
    
            st.markdown("<div style='margin: 15px 0;'></div>", unsafe_allow_html=True)
    
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

    # Hugging Face 토큰 검출 안전 장치 (세션 상태 또는 secrets.toml)
    hf_active = False
    if st.session_state.get("hf_token", ""):
        hf_active = True
    else:
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
