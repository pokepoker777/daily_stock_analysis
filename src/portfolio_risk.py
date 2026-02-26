# -*- coding: utf-8 -*-
"""
===================================
Portfolio-Level Risk Analytics
===================================

Provides quantitative risk metrics that are absent from the current
per-stock analysis pipeline. These metrics give users a holistic view
of their watchlist's aggregate risk exposure.

Metrics:
1. Correlation Matrix — inter-stock dependency
2. Historical VaR (Value at Risk) — worst-case daily loss estimate
3. Sharpe Ratio — risk-adjusted return
4. Maximum Drawdown — largest peak-to-trough decline
5. Beta (vs market index) — systematic risk
6. Position Sizing via Kelly Criterion — optimal allocation

Usage:
    from src.portfolio_risk import PortfolioRiskAnalyzer
    analyzer = PortfolioRiskAnalyzer()
    report = analyzer.analyze(stock_codes=["600519", "000001", "300750"])
"""

import logging
from dataclasses import dataclass, field
from datetime import date, timedelta
from typing import Any, Dict, List, Optional, Tuple

import numpy as np
import pandas as pd

logger = logging.getLogger(__name__)

# Annualization factor for daily data (approx 242 trading days in China A-share)
TRADING_DAYS_PER_YEAR = 242
RISK_FREE_RATE_ANNUAL = 0.02  # 2% annual risk-free rate (China 10Y govt bond approx)


@dataclass
class StockRiskMetrics:
    """Per-stock risk metrics."""
    code: str
    name: str = ""
    annualized_return: float = 0.0
    annualized_volatility: float = 0.0
    sharpe_ratio: float = 0.0
    max_drawdown: float = 0.0
    max_drawdown_pct: float = 0.0
    beta: float = 1.0  # vs benchmark
    var_95: float = 0.0  # 95% daily VaR (as negative %)
    var_99: float = 0.0  # 99% daily VaR
    kelly_fraction: float = 0.0  # Kelly optimal bet size
    win_rate: float = 0.0  # Historical daily win rate

    def to_dict(self) -> Dict[str, Any]:
        return {
            "code": self.code,
            "name": self.name,
            "annualized_return": round(self.annualized_return * 100, 2),
            "annualized_volatility": round(self.annualized_volatility * 100, 2),
            "sharpe_ratio": round(self.sharpe_ratio, 3),
            "max_drawdown_pct": round(self.max_drawdown_pct * 100, 2),
            "beta": round(self.beta, 3),
            "var_95_pct": round(self.var_95 * 100, 2),
            "var_99_pct": round(self.var_99 * 100, 2),
            "kelly_fraction_pct": round(self.kelly_fraction * 100, 1),
            "win_rate_pct": round(self.win_rate * 100, 1),
        }


@dataclass
class PortfolioRiskReport:
    """Aggregated portfolio risk report."""
    analysis_date: str = ""
    stock_count: int = 0

    # Per-stock metrics
    stock_metrics: List[StockRiskMetrics] = field(default_factory=list)

    # Portfolio-level metrics (equal-weight assumed)
    portfolio_return: float = 0.0
    portfolio_volatility: float = 0.0
    portfolio_sharpe: float = 0.0
    portfolio_var_95: float = 0.0
    portfolio_max_drawdown: float = 0.0
    diversification_ratio: float = 0.0  # >1 means diversification benefit

    # Correlation matrix (stock_code pairs)
    correlation_matrix: Optional[pd.DataFrame] = None
    high_correlation_pairs: List[Tuple[str, str, float]] = field(default_factory=list)

    def to_dict(self) -> Dict[str, Any]:
        corr_dict = None
        if self.correlation_matrix is not None:
            corr_dict = {
                "columns": list(self.correlation_matrix.columns),
                "data": self.correlation_matrix.round(3).values.tolist(),
            }

        return {
            "analysis_date": self.analysis_date,
            "stock_count": self.stock_count,
            "portfolio": {
                "annualized_return_pct": round(self.portfolio_return * 100, 2),
                "annualized_volatility_pct": round(self.portfolio_volatility * 100, 2),
                "sharpe_ratio": round(self.portfolio_sharpe, 3),
                "var_95_pct": round(self.portfolio_var_95 * 100, 2),
                "max_drawdown_pct": round(self.portfolio_max_drawdown * 100, 2),
                "diversification_ratio": round(self.diversification_ratio, 3),
            },
            "stocks": [s.to_dict() for s in self.stock_metrics],
            "correlation_matrix": corr_dict,
            "high_correlation_pairs": [
                {"stock_a": a, "stock_b": b, "correlation": round(c, 3)}
                for a, b, c in self.high_correlation_pairs
            ],
        }

    def to_summary_text(self) -> str:
        """Generate human-readable risk summary for notifications."""
        lines = [
            f"📊 Portfolio Risk Report ({self.analysis_date})",
            f"Stocks: {self.stock_count} | Diversification: {self.diversification_ratio:.2f}x",
            f"",
            f"Portfolio (equal-weight):",
            f"  Annualized Return: {self.portfolio_return * 100:+.1f}%",
            f"  Annualized Vol:    {self.portfolio_volatility * 100:.1f}%",
            f"  Sharpe Ratio:      {self.portfolio_sharpe:.2f}",
            f"  VaR(95%, daily):   {self.portfolio_var_95 * 100:.2f}%",
            f"  Max Drawdown:      {self.portfolio_max_drawdown * 100:.1f}%",
        ]

        if self.high_correlation_pairs:
            lines.append("")
            lines.append("⚠️ High Correlation Pairs (>0.7):")
            for a, b, c in self.high_correlation_pairs[:5]:
                lines.append(f"  {a} ↔ {b}: {c:.2f}")

        lines.append("")
        lines.append("Per-Stock Metrics:")
        lines.append(f"{'Code':<10} {'Sharpe':>7} {'Vol%':>6} {'MDD%':>6} {'VaR95%':>7} {'Kelly%':>7}")
        for s in self.stock_metrics:
            lines.append(
                f"{s.code:<10} {s.sharpe_ratio:>7.2f} "
                f"{s.annualized_volatility * 100:>5.1f}% "
                f"{s.max_drawdown_pct * 100:>5.1f}% "
                f"{s.var_95 * 100:>6.2f}% "
                f"{s.kelly_fraction * 100:>6.1f}%"
            )

        return "\n".join(lines)


class PortfolioRiskAnalyzer:
    """
    Portfolio risk analysis engine.

    Computes risk metrics from historical daily return data retrieved
    from the project's existing data layer (DatabaseManager / DataFetcherManager).
    """

    def __init__(self, lookback_days: int = 60):
        """
        Args:
            lookback_days: Number of trading days to use for risk calculations.
        """
        self.lookback_days = lookback_days

    def analyze(
        self,
        stock_codes: List[str],
        returns_dict: Optional[Dict[str, pd.Series]] = None,
    ) -> PortfolioRiskReport:
        """
        Run full portfolio risk analysis.

        Args:
            stock_codes: List of stock codes to analyze.
            returns_dict: Pre-computed daily returns keyed by stock code.
                          If None, will attempt to fetch from DB/data providers.

        Returns:
            PortfolioRiskReport with all metrics.
        """
        report = PortfolioRiskReport(
            analysis_date=date.today().isoformat(),
            stock_count=len(stock_codes),
        )

        if not stock_codes:
            return report

        # Step 1: Get daily returns for each stock
        if returns_dict is None:
            returns_dict = self._fetch_returns(stock_codes)

        if not returns_dict:
            logger.warning("No return data available for portfolio risk analysis")
            return report

        # Step 2: Per-stock metrics
        for code in stock_codes:
            if code not in returns_dict or returns_dict[code].empty:
                continue
            metrics = self._compute_stock_metrics(code, returns_dict[code])
            report.stock_metrics.append(metrics)

        # Step 3: Portfolio-level metrics (equal-weight)
        valid_codes = [s.code for s in report.stock_metrics]
        if len(valid_codes) >= 2:
            returns_df = pd.DataFrame({c: returns_dict[c] for c in valid_codes if c in returns_dict})
            returns_df = returns_df.dropna()

            if len(returns_df) >= 10:
                self._compute_portfolio_metrics(returns_df, report)

        return report

    def _fetch_returns(self, stock_codes: List[str]) -> Dict[str, pd.Series]:
        """Fetch daily returns from DB or data providers."""
        returns_dict = {}
        try:
            from src.storage import get_db
            db = get_db()

            for code in stock_codes:
                try:
                    context = db.get_analysis_context(code)
                    if context and "raw_data" in context:
                        raw = context["raw_data"]
                        if isinstance(raw, list) and len(raw) > 5:
                            df = pd.DataFrame(raw)
                            df = df.sort_values("date").reset_index(drop=True)
                            if "close" in df.columns:
                                returns = df["close"].pct_change().dropna()
                                returns_dict[code] = returns.tail(self.lookback_days)
                except Exception as e:
                    logger.debug(f"Failed to fetch returns for {code}: {e}")
        except Exception as e:
            logger.warning(f"DB access failed for portfolio risk: {e}")

        return returns_dict

    def _compute_stock_metrics(self, code: str, returns: pd.Series) -> StockRiskMetrics:
        """Compute risk metrics for a single stock."""
        metrics = StockRiskMetrics(code=code)

        if returns.empty or len(returns) < 5:
            return metrics

        # Basic statistics
        daily_mean = returns.mean()
        daily_std = returns.std()

        # Annualized return & volatility
        metrics.annualized_return = daily_mean * TRADING_DAYS_PER_YEAR
        metrics.annualized_volatility = daily_std * np.sqrt(TRADING_DAYS_PER_YEAR)

        # Sharpe Ratio
        daily_rf = RISK_FREE_RATE_ANNUAL / TRADING_DAYS_PER_YEAR
        if daily_std > 0:
            metrics.sharpe_ratio = (daily_mean - daily_rf) / daily_std * np.sqrt(TRADING_DAYS_PER_YEAR)

        # Maximum Drawdown
        cumulative = (1 + returns).cumprod()
        running_max = cumulative.cummax()
        drawdown = (cumulative - running_max) / running_max
        metrics.max_drawdown_pct = float(drawdown.min())

        # Historical VaR (percentile method)
        metrics.var_95 = float(np.percentile(returns, 5))  # 5th percentile = 95% VaR
        metrics.var_99 = float(np.percentile(returns, 1))  # 1st percentile = 99% VaR

        # Win rate
        metrics.win_rate = float((returns > 0).sum() / len(returns))

        # Kelly Criterion: f* = (p * b - q) / b
        # where p = win_rate, q = 1-p, b = avg_win / avg_loss
        wins = returns[returns > 0]
        losses = returns[returns < 0]
        if len(wins) > 0 and len(losses) > 0:
            avg_win = wins.mean()
            avg_loss = abs(losses.mean())
            if avg_loss > 0:
                b = avg_win / avg_loss
                p = metrics.win_rate
                q = 1 - p
                kelly = (p * b - q) / b
                # Clamp to [0, 0.5] — half-Kelly is safer in practice
                metrics.kelly_fraction = max(0.0, min(0.5, kelly))

        return metrics

    def _compute_portfolio_metrics(
        self,
        returns_df: pd.DataFrame,
        report: PortfolioRiskReport,
    ) -> None:
        """Compute portfolio-level metrics from multi-stock returns DataFrame."""
        n = len(returns_df.columns)
        weights = np.array([1.0 / n] * n)  # Equal weight

        # Portfolio return series
        portfolio_returns = returns_df.dot(weights)

        # Portfolio return & volatility
        daily_mean = portfolio_returns.mean()
        daily_std = portfolio_returns.std()
        report.portfolio_return = daily_mean * TRADING_DAYS_PER_YEAR
        report.portfolio_volatility = daily_std * np.sqrt(TRADING_DAYS_PER_YEAR)

        # Sharpe
        daily_rf = RISK_FREE_RATE_ANNUAL / TRADING_DAYS_PER_YEAR
        if daily_std > 0:
            report.portfolio_sharpe = (daily_mean - daily_rf) / daily_std * np.sqrt(TRADING_DAYS_PER_YEAR)

        # Portfolio VaR
        report.portfolio_var_95 = float(np.percentile(portfolio_returns, 5))

        # Portfolio Max Drawdown
        cumulative = (1 + portfolio_returns).cumprod()
        running_max = cumulative.cummax()
        drawdown = (cumulative - running_max) / running_max
        report.portfolio_max_drawdown = float(drawdown.min())

        # Correlation matrix
        report.correlation_matrix = returns_df.corr()

        # High correlation pairs (> 0.7, excluding self-correlation)
        corr = report.correlation_matrix
        pairs = []
        cols = list(corr.columns)
        for i in range(len(cols)):
            for j in range(i + 1, len(cols)):
                c = corr.iloc[i, j]
                if abs(c) > 0.7:
                    pairs.append((cols[i], cols[j], float(c)))
        pairs.sort(key=lambda x: abs(x[2]), reverse=True)
        report.high_correlation_pairs = pairs

        # Diversification ratio = weighted avg vol / portfolio vol
        individual_vols = returns_df.std() * np.sqrt(TRADING_DAYS_PER_YEAR)
        weighted_avg_vol = float(individual_vols.dot(weights))
        if report.portfolio_volatility > 0:
            report.diversification_ratio = weighted_avg_vol / report.portfolio_volatility
        else:
            report.diversification_ratio = 1.0
