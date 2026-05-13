"""
StockInsight Omni - AI 예측 모듈
Prophet 기반 주가 예측, 기대 수익률 범위, 투자 매력도 시각화
"""
import streamlit as st
import pandas as pd
import numpy as np
import plotly.graph_objects as go
from config import COLORS


class StockPredictor:
    """Prophet 기반 주가 예측 엔진"""

    def __init__(self):
        self.model = None
        self.forecast = None
        self.df_train = None
        self.ticker = None

    @st.cache_data(ttl=1800, show_spinner=False)
    def _fit_and_predict(_self, ticker: str, period: str = "5y",
                         forecast_days: int = 90) -> tuple:
        """모델 학습 및 예측 (30분 캐싱)"""
        import os
        import tempfile
        from data_fetcher import get_stock_data

        # ──────────────────────────────────────────────────────────────
        # 윈도우 한글 사용자 계정 오류 방지 (cmdstanpy 한글 경로 버그 우회)
        # ──────────────────────────────────────────────────────────────
        original_env = {}
        safe_temp = None
        if os.name == 'nt':
            try:
                safe_temp = "C:\\Users\\Public\\StockInsight_Temp"
                os.makedirs(safe_temp, exist_ok=True)
                for var in ['TMPDIR', 'TEMP', 'TMP']:
                    original_env[var] = os.environ.get(var)
                    os.environ[var] = safe_temp
                # 파이썬의 임시 폴더 캐시도 강제 변경
                tempfile.tempdir = safe_temp
            except Exception:
                safe_temp = None

        from prophet import Prophet

        df = get_stock_data(ticker, period)
        if df.empty or len(df) < 60:
            # 환경 변수 복원
            if safe_temp:
                for var, val in original_env.items():
                    if val is not None:
                        os.environ[var] = val
                    else:
                        os.environ.pop(var, None)
            return None, None, None

        # Prophet 포맷으로 변환
        df_train = df[["Close"]].reset_index()
        df_train.columns = ["ds", "y"]
        df_train["ds"] = pd.to_datetime(df_train["ds"]).dt.tz_localize(None)

        try:
            # 모델 학습
            model = Prophet(
                daily_seasonality=False,
                weekly_seasonality=True,
                yearly_seasonality=True,
                changepoint_prior_scale=0.05,
            )
            model.fit(df_train)

            # 예측
            future = model.make_future_dataframe(periods=forecast_days)
            forecast = model.predict(future)
        finally:
            # 작업이 끝나면 환경 변수 원래대로 안전하게 복구
            if safe_temp:
                for var, val in original_env.items():
                    if val is not None:
                        os.environ[var] = val
                    else:
                        os.environ.pop(var, None)
                tempfile.tempdir = None

        return model, forecast, df_train

    def predict(self, ticker: str, period: str = "5y",
                forecast_days: int = 90) -> bool:
        """예측 실행"""
        self.ticker = ticker
        result = self._fit_and_predict(ticker, period, forecast_days)
        if result[0] is None:
            return False
        self.model, self.forecast, self.df_train = result
        return True

    def get_expected_return_range(self) -> dict:
        """기대 수익률 범위 계산"""
        if self.forecast is None or self.df_train is None:
            return {}

        current_price = float(self.df_train["y"].iloc[-1])
        future_only = self.forecast[self.forecast["ds"] > self.df_train["ds"].max()]

        if future_only.empty:
            return {}

        last_forecast = future_only.iloc[-1]
        expected = float(last_forecast["yhat"])
        upper = float(last_forecast["yhat_upper"])
        lower = float(last_forecast["yhat_lower"])

        return {
            "current_price": current_price,
            "expected_price": expected,
            "upper_price": upper,
            "lower_price": lower,
            "expected_return": ((expected - current_price) / current_price) * 100,
            "best_case_return": ((upper - current_price) / current_price) * 100,
            "worst_case_return": ((lower - current_price) / current_price) * 100,
        }

    def get_investment_attractiveness(self) -> dict:
        """투자 매력도 점수 계산 (0~100)"""
        ret = self.get_expected_return_range()
        if not ret:
            return {"score": 50, "label": "분석 불가", "color": "#8b92a5"}

        score = 50.0  # 기본 점수

        # 1. 기대 수익률 기반 (±25점)
        exp_ret = ret["expected_return"]
        score += min(max(exp_ret * 2.5, -25), 25)

        # 2. 변동성 (범위 좁을수록 유리, ±15점)
        spread = ret["best_case_return"] - ret["worst_case_return"]
        if spread < 20:
            score += 15
        elif spread < 40:
            score += 5
        else:
            score -= 10

        # 3. 하방 리스크 (±10점)
        if ret["worst_case_return"] > -5:
            score += 10
        elif ret["worst_case_return"] > -15:
            score += 0
        else:
            score -= 10

        score = min(max(score, 0), 100)

        if score >= 70:
            label, color = "매력적 🟢", COLORS["bullish"]
        elif score >= 40:
            label, color = "보통 🟡", COLORS["accent_gold"]
        else:
            label, color = "주의 🔴", COLORS["bearish"]

        return {"score": round(score), "label": label, "color": color}

    def create_forecast_chart(self) -> go.Figure:
        """예측 결과 시각화"""
        if self.forecast is None or self.df_train is None:
            return go.Figure()

        fig = go.Figure()

        # 실제 데이터
        fig.add_trace(go.Scatter(
            x=self.df_train["ds"], y=self.df_train["y"],
            name="실제 주가", mode="lines",
            line=dict(color=COLORS["text_primary"], width=1.5),
        ))

        # 예측선
        fig.add_trace(go.Scatter(
            x=self.forecast["ds"], y=self.forecast["yhat"],
            name="예측", mode="lines",
            line=dict(color=COLORS["accent_blue"], width=2, dash="dot"),
        ))

        # 신뢰 구간
        fig.add_trace(go.Scatter(
            x=self.forecast["ds"], y=self.forecast["yhat_upper"],
            name="상한", mode="lines",
            line=dict(width=0), showlegend=False,
        ))
        fig.add_trace(go.Scatter(
            x=self.forecast["ds"], y=self.forecast["yhat_lower"],
            name="신뢰 구간", mode="lines",
            line=dict(width=0),
            fill="tonexty", fillcolor="rgba(56,97,251,0.1)",
        ))

        # 현재 시점 구분선
        last_date = self.df_train["ds"].max().to_pydatetime()
        fig.add_vline(
            x=last_date, line_dash="dash",
            line_color=COLORS["accent_gold"], opacity=0.5,
        )
        fig.add_annotation(
            x=last_date,
            y=0.98,
            yref="paper",
            text="현재",
            showarrow=False,
            xanchor="right",
            font=dict(color=COLORS["accent_gold"], size=11),
            bgcolor="rgba(10,14,39,0.8)",
        )

        fig.update_layout(
            template="plotly_dark",
            paper_bgcolor="rgba(0,0,0,0)",
            plot_bgcolor="rgba(10,14,39,0.8)",
            font=dict(family="Inter, Noto Sans KR", color=COLORS["text_secondary"]),
            height=500,
            margin=dict(l=50, r=20, t=40, b=40),
            xaxis=dict(gridcolor="rgba(56,97,251,0.06)"),
            yaxis=dict(gridcolor="rgba(56,97,251,0.06)", title="주가"),
            legend=dict(
                bgcolor="rgba(0,0,0,0)", font=dict(size=11),
                orientation="h", yanchor="bottom", y=1.02, xanchor="right", x=1,
            ),
            hovermode="x unified",
        )
        return fig

    def create_gauge_chart(self) -> go.Figure:
        """투자 매력도 게이지 차트"""
        attractiveness = self.get_investment_attractiveness()
        score = attractiveness["score"]

        fig = go.Figure(go.Indicator(
            mode="gauge+number",
            value=score,
            number=dict(font=dict(size=48, color=COLORS["text_primary"])),
            title=dict(
                text=f"투자 매력도: {attractiveness['label']}",
                font=dict(size=16, color=COLORS["text_secondary"]),
            ),
            gauge=dict(
                axis=dict(range=[0, 100], tickcolor=COLORS["text_muted"]),
                bar=dict(color=attractiveness["color"]),
                bgcolor="rgba(18,22,56,0.8)",
                borderwidth=0,
                steps=[
                    dict(range=[0, 30], color="rgba(255,71,87,0.15)"),
                    dict(range=[30, 60], color="rgba(240,185,11,0.15)"),
                    dict(range=[60, 100], color="rgba(0,212,170,0.15)"),
                ],
                threshold=dict(
                    line=dict(color=COLORS["text_primary"], width=2),
                    thickness=0.8, value=score,
                ),
            ),
        ))

        fig.update_layout(
            height=300,
            paper_bgcolor="rgba(0,0,0,0)",
            plot_bgcolor="rgba(0,0,0,0)",
            font=dict(family="Inter, Noto Sans KR", color=COLORS["text_secondary"]),
            margin=dict(l=30, r=30, t=60, b=20),
        )
        return fig

    def create_return_range_chart(self) -> go.Figure:
        """기대 수익률 범위 바 차트"""
        ret = self.get_expected_return_range()
        if not ret:
            return go.Figure()

        categories = ["최악 시나리오", "기대 수익률", "최선 시나리오"]
        values = [ret["worst_case_return"], ret["expected_return"], ret["best_case_return"]]
        colors = [COLORS["bearish"], COLORS["accent_blue"], COLORS["bullish"]]

        fig = go.Figure()
        fig.add_trace(go.Bar(
            x=categories, y=values,
            marker_color=colors,
            text=[f"{v:+.1f}%" for v in values],
            textposition="outside",
            textfont=dict(size=14, color=COLORS["text_primary"]),
        ))

        fig.add_hline(y=0, line_color=COLORS["text_muted"], opacity=0.3)

        fig.update_layout(
            template="plotly_dark",
            paper_bgcolor="rgba(0,0,0,0)",
            plot_bgcolor="rgba(10,14,39,0.8)",
            font=dict(family="Inter, Noto Sans KR", color=COLORS["text_secondary"]),
            height=350,
            margin=dict(l=40, r=20, t=30, b=40),
            yaxis=dict(title="수익률 (%)", gridcolor="rgba(56,97,251,0.06)"),
            xaxis=dict(gridcolor="rgba(56,97,251,0.06)"),
            showlegend=False,
        )
        return fig
