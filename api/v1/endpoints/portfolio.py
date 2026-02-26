# -*- coding: utf-8 -*-
"""
===================================
Portfolio Risk Analysis API Endpoint
===================================

Provides portfolio-level risk metrics including:
- Per-stock: Sharpe, VaR, Max Drawdown, Kelly Criterion
- Portfolio: Correlation matrix, diversification ratio
- Risk alerts for highly correlated pairs
"""

import logging
from typing import List, Optional

from fastapi import APIRouter, Depends, HTTPException, Query

from api.deps import get_config_dep
from src.config import Config

logger = logging.getLogger(__name__)

router = APIRouter()


@router.get(
    "/risk",
    summary="Portfolio risk analysis",
    description="Compute portfolio-level risk metrics for the configured stock list or specified codes.",
)
async def get_portfolio_risk(
    codes: Optional[str] = Query(
        None,
        description="Comma-separated stock codes. If omitted, uses configured STOCK_LIST.",
        example="600519,000001,300750",
    ),
    lookback: int = Query(
        60,
        ge=10,
        le=250,
        description="Number of trading days for risk calculations.",
    ),
    config: Config = Depends(get_config_dep),
):
    """
    Run portfolio risk analysis and return metrics.

    Returns per-stock metrics (Sharpe, VaR, Max Drawdown, Kelly),
    portfolio-level metrics (correlation, diversification ratio),
    and risk alerts for highly correlated pairs.
    """
    try:
        from src.portfolio_risk import PortfolioRiskAnalyzer

        # Determine stock codes
        if codes:
            stock_codes = [c.strip() for c in codes.split(",") if c.strip()]
        else:
            stock_codes = config.stock_list

        if not stock_codes:
            raise HTTPException(
                status_code=400,
                detail={
                    "error": "no_stocks",
                    "message": "No stock codes provided. Set STOCK_LIST or pass ?codes=600519,000001",
                },
            )

        analyzer = PortfolioRiskAnalyzer(lookback_days=lookback)
        report = analyzer.analyze(stock_codes=stock_codes)

        return {
            "success": True,
            "data": report.to_dict(),
            "summary": report.to_summary_text(),
        }

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Portfolio risk analysis failed: {e}", exc_info=True)
        raise HTTPException(
            status_code=500,
            detail={
                "error": "analysis_failed",
                "message": f"Portfolio risk analysis failed: {str(e)[:200]}",
            },
        )


@router.get(
    "/risk/summary",
    summary="Portfolio risk summary (text)",
    description="Returns a plain-text risk summary suitable for notifications.",
)
async def get_portfolio_risk_summary(
    codes: Optional[str] = Query(None),
    lookback: int = Query(60, ge=10, le=250),
    config: Config = Depends(get_config_dep),
):
    """Return plain-text risk summary for notification integration."""
    try:
        from src.portfolio_risk import PortfolioRiskAnalyzer

        stock_codes = [c.strip() for c in codes.split(",") if c.strip()] if codes else config.stock_list

        if not stock_codes:
            return {"success": False, "summary": "No stock codes configured."}

        analyzer = PortfolioRiskAnalyzer(lookback_days=lookback)
        report = analyzer.analyze(stock_codes=stock_codes)

        return {
            "success": True,
            "summary": report.to_summary_text(),
        }

    except Exception as e:
        logger.error(f"Portfolio risk summary failed: {e}", exc_info=True)
        return {
            "success": False,
            "summary": f"Error: {str(e)[:200]}",
        }
