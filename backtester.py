"""
StockInsight Omni - 포트폴리오 백테스트 모듈
수익률, MDD, 샤프지수, 벤치마크 비교, 시각화
"""
import pandas as pd
import numpy as np
import plotly.graph_objects as go
from plotly.subplots import make_subplots
from config import COLORS, BACKTEST_DEFAULTS
import streamlit as st


class PortfolioBacktester:
    """포트폴리오 백테스트 엔진"""

    def __init__(self):
        self.tickers = []
        self.weights = []
        self.start_date = None
        self.end_date = None
        self.initial_capital = BACKTEST_DEFAULTS["initial_capital"]
        self.risk_free_rate = BACKTEST_DEFAULTS["risk_free_rate"]
        self.portfolio_returns = None
        self.portfolio_value = None
        self.benchmark_returns = None
        self.benchmark_value = None
        self.metrics = {}

    def set_portfolio(self, tickers: list, weights: list,
                      start_date: str, end_date: str = None,
                      initial_capital: float = None):
        """포트폴리오 구성 설정"""
        self.tickers = tickers
        self.weights = np.array(weights) / np.sum(weights)  # 정규화
        self.start_date = start_date
        self.end_date = end_date
        if initial_capital:
            self.initial_capital = initial_capital

    @st.cache_data(ttl=600, show_spinner=False)
    def _fetch_data(_self, tickers: tuple, start: str, end: str) -> pd.DataFrame:
        """주가 데이터 수집"""
        import yfinance as yf
        try:
            data = yf.download(
                list(tickers), start=start, end=end,
                auto_adjust=True, progress=False,
            )
            if data.empty:
                return pd.DataFrame()
            if "Close" in data.columns or (hasattr(data.columns, 'get_level_values') and "Close" in data.columns.get_level_values(0)):
                if len(tickers) == 1:
                    if isinstance(data.columns, pd.MultiIndex):
                        prices = data["Close"]
                    else:
                        prices = data[["Close"]]
                        prices.columns = [tickers[0]]
                else:
                    prices = data["Close"]
            else:
                prices = data
            return prices.dropna()
        except Exception:
            return pd.DataFrame()

    def run_backtest(self) -> bool:
        """백테스트 실행"""
        prices = self._fetch_data(
            tuple(self.tickers), self.start_date, self.end_date
        )
        if prices.empty:
            return False

        # 일일 수익률
        daily_returns = prices.pct_change().dropna()

        # 포트폴리오 가중 수익률
        if len(self.tickers) == 1:
            if isinstance(daily_returns, pd.DataFrame):
                self.portfolio_returns = daily_returns.iloc[:, 0]
            else:
                self.portfolio_returns = daily_returns
        else:
            self.portfolio_returns = (daily_returns * self.weights).sum(axis=1)

        # 포트폴리오 누적 가치
        self.portfolio_value = (
            (1 + self.portfolio_returns).cumprod() * self.initial_capital
        )

        # 메트릭 계산
        self._calculate_metrics()
        return True

    def compare_benchmark(self, benchmark_ticker: str = None) -> bool:
        """벤치마크 비교"""
        if benchmark_ticker is None:
            benchmark_ticker = BACKTEST_DEFAULTS["benchmark_ticker"]

        prices = self._fetch_data(
            (benchmark_ticker,), self.start_date, self.end_date
        )
        if prices.empty:
            return False

        if isinstance(prices, pd.DataFrame):
            bench_returns = prices.iloc[:, 0].pct_change().dropna()
        else:
            bench_returns = prices.pct_change().dropna()

        # 포트폴리오와 동일 기간 정렬
        common_idx = self.portfolio_returns.index.intersection(bench_returns.index)
        self.benchmark_returns = bench_returns.loc[common_idx]
        self.benchmark_value = (
            (1 + self.benchmark_returns).cumprod() * self.initial_capital
        )
        return True

    def _calculate_metrics(self):
        """핵심 성과 지표 계산"""
        ret = self.portfolio_returns
        if ret is None or len(ret) < 2:
            return

        trading_days = 252
        total_days = (ret.index[-1] - ret.index[0]).days
        years = total_days / 365.25

        # 총 수익률
        total_return = float((1 + ret).prod() - 1)

        # CAGR
        if years > 0:
            cagr = float((1 + total_return) ** (1 / years) - 1)
        else:
            cagr = total_return

        # 변동성
        volatility = float(ret.std() * np.sqrt(trading_days))

        # 샤프 지수
        excess = ret.mean() - self.risk_free_rate / trading_days
        sharpe = float(excess / ret.std() * np.sqrt(trading_days)) if ret.std() > 0 else 0

        # 소르티노 비율
        downside = ret[ret < 0]
        downside_std = float(downside.std() * np.sqrt(trading_days)) if len(downside) > 0 else 1
        sortino = float(excess * np.sqrt(trading_days) / downside_std) if downside_std > 0 else 0

        # MDD
        cummax = (1 + ret).cumprod().cummax()
        drawdown = (1 + ret).cumprod() / cummax - 1
        mdd = float(drawdown.min())
        mdd_end = drawdown.idxmin()

        self.metrics = {
            "total_return": total_return,
            "cagr": cagr,
            "volatility": volatility,
            "sharpe": sharpe,
            "sortino": sortino,
            "mdd": mdd,
            "mdd_date": mdd_end,
            "total_days": total_days,
            "years": years,
        }

    def create_cumulative_chart(self) -> go.Figure:
        """누적 수익률 비교 차트"""
        fig = go.Figure()

        if self.portfolio_value is not None:
            fig.add_trace(go.Scatter(
                x=self.portfolio_value.index,
                y=self.portfolio_value.values,
                name="포트폴리오",
                line=dict(color=COLORS["accent_blue"], width=2.5),
                fill="tozeroy",
                fillcolor="rgba(56,97,251,0.06)",
            ))

        if self.benchmark_value is not None:
            fig.add_trace(go.Scatter(
                x=self.benchmark_value.index,
                y=self.benchmark_value.values,
                name="벤치마크",
                line=dict(color=COLORS["accent_gold"], width=2, dash="dash"),
            ))

        fig.update_layout(
            template="plotly_dark",
            paper_bgcolor="rgba(0,0,0,0)",
            plot_bgcolor="rgba(10,14,39,0.8)",
            font=dict(family="Inter, Noto Sans KR", color=COLORS["text_secondary"]),
            height=450,
            margin=dict(l=50, r=20, t=40, b=40),
            xaxis=dict(gridcolor="rgba(56,97,251,0.06)"),
            yaxis=dict(gridcolor="rgba(56,97,251,0.06)", title="포트폴리오 가치"),
            legend=dict(
                bgcolor="rgba(0,0,0,0)", font=dict(size=11),
                orientation="h", yanchor="bottom", y=1.02, xanchor="right", x=1,
            ),
            hovermode="x unified",
        )
        return fig

    def create_drawdown_chart(self) -> go.Figure:
        """Drawdown 차트"""
        if self.portfolio_returns is None:
            return go.Figure()

        cummax = (1 + self.portfolio_returns).cumprod().cummax()
        drawdown = ((1 + self.portfolio_returns).cumprod() / cummax - 1) * 100

        fig = go.Figure()
        fig.add_trace(go.Scatter(
            x=drawdown.index, y=drawdown.values,
            name="Drawdown", mode="lines",
            line=dict(color=COLORS["bearish"], width=1.5),
            fill="tozeroy", fillcolor="rgba(255,71,87,0.1)",
        ))

        fig.add_hline(y=0, line_color=COLORS["text_muted"], opacity=0.3)

        fig.update_layout(
            template="plotly_dark",
            paper_bgcolor="rgba(0,0,0,0)",
            plot_bgcolor="rgba(10,14,39,0.8)",
            font=dict(family="Inter, Noto Sans KR", color=COLORS["text_secondary"]),
            height=300,
            margin=dict(l=50, r=20, t=30, b=40),
            xaxis=dict(gridcolor="rgba(56,97,251,0.06)"),
            yaxis=dict(gridcolor="rgba(56,97,251,0.06)", title="Drawdown (%)"),
            showlegend=False,
            hovermode="x unified",
        )
        return fig

    def create_monthly_heatmap(self) -> go.Figure:
        """월별 수익률 히트맵"""
        if self.portfolio_returns is None:
            return go.Figure()

        monthly = self.portfolio_returns.resample("ME").apply(
            lambda x: (1 + x).prod() - 1
        ) * 100

        # 연-월 피벗
        df = pd.DataFrame({
            "year": monthly.index.year,
            "month": monthly.index.month,
            "return": monthly.values,
        })
        pivot = df.pivot_table(values="return", index="year", columns="month")
        pivot.columns = ["1월","2월","3월","4월","5월","6월",
                         "7월","8월","9월","10월","11월","12월"][:len(pivot.columns)]

        fig = go.Figure(data=go.Heatmap(
            z=pivot.values,
            x=pivot.columns,
            y=pivot.index,
            colorscale=[
                [0, COLORS["bearish"]],
                [0.5, "#1a1f48"],
                [1, COLORS["bullish"]],
            ],
            text=[[f"{v:.1f}%" if not np.isnan(v) else "" for v in row] for row in pivot.values],
            texttemplate="%{text}",
            textfont=dict(size=10),
            hovertemplate="<b>%{y}년 %{x}</b><br>수익률: %{z:.2f}%<extra></extra>",
            colorbar=dict(title="수익률 (%)"),
        ))

        fig.update_layout(
            template="plotly_dark",
            paper_bgcolor="rgba(0,0,0,0)",
            plot_bgcolor="rgba(10,14,39,0.8)",
            font=dict(family="Inter, Noto Sans KR", color=COLORS["text_secondary"]),
            height=max(250, len(pivot) * 40 + 80),
            margin=dict(l=50, r=20, t=30, b=40),
        )
        return fig
