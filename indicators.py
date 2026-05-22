"""
StockInsight Omni - 기술적 분석 지표 모듈
이동평균선, RSI, MACD, 볼린저 밴드 계산 및 Plotly 시각화
"""
import pandas as pd
import numpy as np
import plotly.graph_objects as go
from plotly.subplots import make_subplots
from config import COLORS


# ══════════════════════════════════════════════
# 지표 계산 함수
# ══════════════════════════════════════════════

def calculate_moving_averages(df: pd.DataFrame, windows: list = None) -> pd.DataFrame:
    """단순 이동평균선(SMA) 계산"""
    if windows is None:
        windows = [5, 20, 60, 120]
    result = df.copy()
    for w in windows:
        if len(result) >= w:
            result[f"SMA_{w}"] = result["Close"].rolling(window=w).mean()
    return result


def calculate_rsi(df: pd.DataFrame, period: int = 14) -> pd.Series:
    """RSI (Relative Strength Index) 계산"""
    close = df["Close"]
    delta = close.diff()
    gain = delta.where(delta > 0, 0.0)
    loss = -delta.where(delta < 0, 0.0)
    avg_gain = gain.rolling(window=period, min_periods=period).mean()
    avg_loss = loss.rolling(window=period, min_periods=period).mean()
    # Wilder's smoothing
    for i in range(period, len(avg_gain)):
        avg_gain.iloc[i] = (avg_gain.iloc[i - 1] * (period - 1) + gain.iloc[i]) / period
        avg_loss.iloc[i] = (avg_loss.iloc[i - 1] * (period - 1) + loss.iloc[i]) / period
    rs = avg_gain / avg_loss
    rsi = 100 - (100 / (1 + rs))
    return rsi


def calculate_macd(df: pd.DataFrame, fast: int = 12, slow: int = 26, signal: int = 9) -> pd.DataFrame:
    """MACD (Moving Average Convergence Divergence) 계산"""
    close = df["Close"]
    ema_fast = close.ewm(span=fast, adjust=False).mean()
    ema_slow = close.ewm(span=slow, adjust=False).mean()
    macd_line = ema_fast - ema_slow
    signal_line = macd_line.ewm(span=signal, adjust=False).mean()
    histogram = macd_line - signal_line
    result = pd.DataFrame({
        "MACD": macd_line,
        "Signal": signal_line,
        "Histogram": histogram,
    }, index=df.index)
    return result


def calculate_bollinger_bands(df: pd.DataFrame, window: int = 20, std_dev: int = 2) -> pd.DataFrame:
    """볼린저 밴드 계산"""
    close = df["Close"]
    sma = close.rolling(window=window).mean()
    std = close.rolling(window=window).std()
    result = pd.DataFrame({
        "BB_Upper": sma + (std * std_dev),
        "BB_Middle": sma,
        "BB_Lower": sma - (std * std_dev),
    }, index=df.index)
    return result


# ══════════════════════════════════════════════
# 차트 생성 함수 (Plotly)
# ══════════════════════════════════════════════

def _get_chart_layout(title="", height=600):
    """공통 차트 레이아웃 설정"""
    return dict(
        title=dict(text=title, font=dict(size=16, color=COLORS["text_primary"])),
        template="plotly_dark",
        paper_bgcolor="rgba(0,0,0,0)",
        plot_bgcolor="rgba(10,14,39,0.8)",
        font=dict(family="Inter, Noto Sans KR", color=COLORS["text_secondary"]),
        height=height,
        margin=dict(l=50, r=20, t=60, b=40),
        xaxis=dict(
            gridcolor="rgba(56,97,251,0.06)",
            rangeslider=dict(visible=False),
            showgrid=True,
        ),
        yaxis=dict(gridcolor="rgba(56,97,251,0.06)", showgrid=True),
        legend=dict(
            bgcolor="rgba(0,0,0,0)",
            font=dict(size=11),
            orientation="h",
            yanchor="bottom", y=1.02, xanchor="right", x=1,
        ),
        hovermode="x unified",
    )


def create_candlestick_chart(
    df: pd.DataFrame,
    ma_windows: list = None,
    show_bb: bool = False,
    indicators: list = None,
) -> go.Figure:
    """캔들 + 이동평균/볼린저 + 보조지표(거래량/RSI/MACD) 통합 차트.

    indicators: ["volume", "rsi", "macd"] 중 표시할 항목 (순서대로 아래에 쌓임)
    모든 subplot은 x축을 공유하므로 줌/이동이 함께 동기화됩니다.
    """
    if ma_windows is None:
        ma_windows = [5, 20, 60]
    if indicators is None:
        indicators = ["volume"]
    # 정규화: 알려진 값만, 입력 순서 유지
    valid = [i for i in ["volume", "rsi", "macd"] if i in indicators]

    # 메인 차트 + 하단 보조지표 row 구성
    row_titles = {"volume": "거래량", "rsi": "RSI", "macd": "MACD"}
    n_sub = len(valid)
    main_h = 0.75 if n_sub <= 1 else (0.60 if n_sub == 2 else 0.50)
    sub_h = (1.0 - main_h) / max(n_sub, 1) if n_sub else 0
    row_heights = [main_h] + [sub_h] * n_sub

    fig = make_subplots(
        rows=1 + n_sub, cols=1, shared_xaxes=True,
        vertical_spacing=0.03,
        row_heights=row_heights,
        subplot_titles=[""] + [row_titles[i] for i in valid],
    )

    # ── 메인: 캔들스틱 ──
    fig.add_trace(go.Candlestick(
        x=df.index, open=df["Open"], high=df["High"],
        low=df["Low"], close=df["Close"],
        increasing_line_color=COLORS["chart_candle_up"],
        decreasing_line_color=COLORS["chart_candle_down"],
        increasing_fillcolor=COLORS["chart_candle_up"],
        decreasing_fillcolor=COLORS["chart_candle_down"],
        name="캔들", showlegend=False,
    ), row=1, col=1)

    # 이동평균선
    df_ma = calculate_moving_averages(df, ma_windows)
    ma_colors = [COLORS["chart_line_1"], COLORS["chart_line_2"],
                 COLORS["chart_line_3"], COLORS["chart_line_4"]]
    for i, w in enumerate(ma_windows):
        col_name = f"SMA_{w}"
        if col_name in df_ma.columns:
            fig.add_trace(go.Scatter(
                x=df_ma.index, y=df_ma[col_name],
                name=f"SMA {w}", line=dict(width=1.5, color=ma_colors[i % len(ma_colors)]),
            ), row=1, col=1)

    # 볼린저 밴드
    if show_bb:
        bb = calculate_bollinger_bands(df)
        fig.add_trace(go.Scatter(
            x=df.index, y=bb["BB_Upper"], name="BB 상단",
            line=dict(width=1, color="rgba(139,92,246,0.5)", dash="dash"),
        ), row=1, col=1)
        fig.add_trace(go.Scatter(
            x=df.index, y=bb["BB_Lower"], name="BB 하단",
            line=dict(width=1, color="rgba(139,92,246,0.5)", dash="dash"),
            fill="tonexty", fillcolor="rgba(139,92,246,0.05)",
        ), row=1, col=1)

    # ── 보조지표 ──
    for idx, ind in enumerate(valid):
        row = 2 + idx

        if ind == "volume" and "Volume" in df.columns:
            colors = [COLORS["chart_candle_up"] if c >= o else COLORS["chart_candle_down"]
                      for o, c in zip(df["Open"], df["Close"])]
            fig.add_trace(go.Bar(
                x=df.index, y=df["Volume"], name="거래량",
                marker_color=colors, opacity=0.5, showlegend=False,
            ), row=row, col=1)

        elif ind == "rsi":
            rsi = calculate_rsi(df)
            fig.add_hrect(y0=70, y1=100, fillcolor="rgba(255,71,87,0.06)",
                          line_width=0, row=row, col=1)
            fig.add_hrect(y0=0, y1=30, fillcolor="rgba(0,212,170,0.06)",
                          line_width=0, row=row, col=1)
            fig.add_hline(y=70, line_dash="dash", line_color=COLORS["bearish"],
                          opacity=0.4, row=row, col=1)
            fig.add_hline(y=30, line_dash="dash", line_color=COLORS["bullish"],
                          opacity=0.4, row=row, col=1)
            fig.add_trace(go.Scatter(
                x=rsi.index, y=rsi.values, name="RSI(14)",
                line=dict(width=1.5, color=COLORS["accent_purple"]),
                showlegend=False,
            ), row=row, col=1)
            fig.update_yaxes(range=[0, 100], row=row, col=1)

        elif ind == "macd":
            macd = calculate_macd(df)
            hist_colors = [COLORS["bullish"] if v >= 0 else COLORS["bearish"]
                           for v in macd["Histogram"]]
            fig.add_trace(go.Bar(
                x=macd.index, y=macd["Histogram"], name="히스토그램",
                marker_color=hist_colors, opacity=0.6, showlegend=False,
            ), row=row, col=1)
            fig.add_trace(go.Scatter(
                x=macd.index, y=macd["MACD"], name="MACD",
                line=dict(width=1.5, color=COLORS["chart_line_1"]),
                showlegend=False,
            ), row=row, col=1)
            fig.add_trace(go.Scatter(
                x=macd.index, y=macd["Signal"], name="Signal",
                line=dict(width=1.5, color=COLORS["chart_line_2"]),
                showlegend=False,
            ), row=row, col=1)
            fig.add_hline(y=0, line_color=COLORS["text_muted"],
                          opacity=0.3, row=row, col=1)

    # 레이아웃: 보조지표 수에 따라 높이 가변
    total_height = 600 + 160 * n_sub
    layout = _get_chart_layout(height=total_height)
    # 추가 y축 스타일 통일
    for i in range(2, 2 + n_sub):
        layout[f"yaxis{i}"] = dict(gridcolor="rgba(56,97,251,0.06)", showgrid=True)
    fig.update_layout(**layout)
    fig.update_xaxes(rangeslider_visible=False)
    return fig


def create_rsi_chart(df: pd.DataFrame, period: int = 14) -> go.Figure:
    """RSI 차트 (30/70 기준선 포함)"""
    rsi = calculate_rsi(df, period)
    fig = go.Figure()

    # 과매수/과매도 영역
    fig.add_hrect(y0=70, y1=100, fillcolor="rgba(255,71,87,0.06)",
                  line_width=0, annotation_text="과매수",
                  annotation_position="top left",
                  annotation_font_color=COLORS["bearish"])
    fig.add_hrect(y0=0, y1=30, fillcolor="rgba(0,212,170,0.06)",
                  line_width=0, annotation_text="과매도",
                  annotation_position="bottom left",
                  annotation_font_color=COLORS["bullish"])

    # 기준선
    fig.add_hline(y=70, line_dash="dash", line_color=COLORS["bearish"], opacity=0.4)
    fig.add_hline(y=50, line_dash="dot", line_color=COLORS["text_muted"], opacity=0.3)
    fig.add_hline(y=30, line_dash="dash", line_color=COLORS["bullish"], opacity=0.4)

    # RSI 라인
    fig.add_trace(go.Scatter(
        x=rsi.index, y=rsi.values, name=f"RSI ({period})",
        line=dict(width=2, color=COLORS["accent_purple"]),
        fill="tozeroy", fillcolor="rgba(139,92,246,0.08)",
    ))

    layout = _get_chart_layout("RSI (Relative Strength Index)", height=300)
    layout["yaxis"]["range"] = [0, 100]
    fig.update_layout(**layout)
    return fig


def create_macd_chart(df: pd.DataFrame) -> go.Figure:
    """MACD 차트 (MACD 라인 + 시그널 + 히스토그램)"""
    macd = calculate_macd(df)
    fig = go.Figure()

    # 히스토그램
    colors = [COLORS["bullish"] if v >= 0 else COLORS["bearish"] for v in macd["Histogram"]]
    fig.add_trace(go.Bar(
        x=macd.index, y=macd["Histogram"], name="히스토그램",
        marker_color=colors, opacity=0.6,
    ))

    # MACD 라인
    fig.add_trace(go.Scatter(
        x=macd.index, y=macd["MACD"], name="MACD",
        line=dict(width=2, color=COLORS["chart_line_1"]),
    ))

    # 시그널 라인
    fig.add_trace(go.Scatter(
        x=macd.index, y=macd["Signal"], name="Signal",
        line=dict(width=2, color=COLORS["chart_line_2"]),
    ))

    fig.add_hline(y=0, line_color=COLORS["text_muted"], opacity=0.3)

    layout = _get_chart_layout("MACD", height=300)
    fig.update_layout(**layout)
    return fig
