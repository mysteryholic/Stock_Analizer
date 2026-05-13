"""
StockInsight Omni - 스타일 & PWA 모듈
커스텀 CSS 주입, PWA 메타태그, 반응형 레이아웃
"""
import streamlit as st


def inject_custom_css():
    """커스텀 CSS와 PWA 메타태그를 Streamlit 앱에 주입"""
    st.markdown("""
    <meta name="apple-mobile-web-app-capable" content="yes">
    <meta name="apple-mobile-web-app-status-bar-style" content="black-translucent">
    <meta name="apple-mobile-web-app-title" content="StockInsight">
    <meta name="mobile-web-app-capable" content="yes">
    <meta name="viewport" content="width=device-width, initial-scale=1.0, maximum-scale=1.0, user-scalable=no">
    <meta name="theme-color" content="#0a0e27">
    <link href="https://fonts.googleapis.com/css2?family=Inter:wght@300;400;500;600;700;800&family=Noto+Sans+KR:wght@300;400;500;600;700&display=swap" rel="stylesheet">
    """, unsafe_allow_html=True)

    # CSS를 별도 파일에서 읽어오기
    import os
    css_path = os.path.join(os.path.dirname(__file__), "style.css")
    if os.path.exists(css_path):
        with open(css_path, "r", encoding="utf-8") as f:
            css = f.read()
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
