"""
StockInsight Omni - 스타일 & PWA 모듈
커스텀 CSS 주입, PWA 메타태그, 반응형 레이아웃
"""
import streamlit as st


@st.cache_data(show_spinner=False)
def _load_css() -> str:
    """style.css를 디스크에서 한 번만 읽어 메모리 캐싱 (매 rerun마다 디스크 I/O 회피)"""
    import os
    css_path = os.path.join(os.path.dirname(__file__), "style.css")
    if os.path.exists(css_path):
        with open(css_path, "r", encoding="utf-8") as f:
            return f.read()
    return ""


def inject_custom_css():
    """커스텀 CSS와 PWA 메타태그를 Streamlit 앱에 주입"""
    # 폰트는 swap·preconnect로 렌더 차단 최소화 (initial-scale=1, 줌 허용해 접근성 개선)
    st.markdown("""
    <meta name="apple-mobile-web-app-capable" content="yes">
    <meta name="apple-mobile-web-app-status-bar-style" content="black-translucent">
    <meta name="apple-mobile-web-app-title" content="StockInsight">
    <meta name="mobile-web-app-capable" content="yes">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <meta name="theme-color" content="#000000">
    <link rel="preconnect" href="https://fonts.googleapis.com">
    <link rel="preconnect" href="https://fonts.gstatic.com" crossorigin>
    <link href="https://fonts.googleapis.com/css2?family=Inter:wght@400;600;700&family=Noto+Sans+KR:wght@400;600;700&display=swap" rel="stylesheet">
    """, unsafe_allow_html=True)

    css = _load_css()
    if css:
        st.markdown(f"<style>{css}</style>", unsafe_allow_html=True)


def render_page_header(title: str, description: str = ""):
    """페이지 상단 그라데이션 헤더 렌더링"""
    desc_html = f"<p>{description}</p>" if description else ""
    st.markdown(f"""
    <div class="page-header animate-fade-in">
        <h1>{title}</h1>
        {desc_html}
    </div>
    """, unsafe_allow_html=True)


def render_metric_card(title, value, delta="", delta_positive=True):
    """커스텀 메트릭 카드 렌더링"""
    delta_class = "delta-positive" if delta_positive else "delta-negative"
    glow_class = "glow-positive" if delta_positive else "glow-negative"
    delta_html = f'<div class="card-delta {delta_class}">{delta}</div>' if delta else ""
    st.markdown(f"""
    <div class="stock-card {glow_class if delta else ''} animate-fade-in">
        <div class="card-title">{title}</div>
        <div class="card-value">{value}</div>
        {delta_html}
    </div>
    """, unsafe_allow_html=True)


def render_disclaimer():
    """투자 면책 조항 렌더링"""
    st.markdown("""
    <div class="disclaimer">
        ⚠️ <strong>면책 조항:</strong> 본 서비스는 정보 제공 목적으로만 제공되며, 투자 권유나 조언이 아닙니다.
        모든 투자 결정은 본인의 판단과 책임 하에 이루어져야 합니다.
        과거 실적이 미래 수익을 보장하지 않습니다.
    </div>
    """, unsafe_allow_html=True)


def render_badge(text, badge_type="free"):
    """배지 HTML 반환 (free / premium)"""
    return f'<span class="badge badge-{badge_type}">{text}</span>'


def render_live_indicator():
    """실시간 표시 인디케이터 HTML"""
    return '<span class="live-indicator"></span> LIVE'
