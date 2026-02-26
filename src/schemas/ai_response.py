# -*- coding: utf-8 -*-
"""
===================================
Pydantic models for AI response validation
===================================

Type-safe parsing of LLM JSON output.
Replaces fragile dict-based access with validated models,
providing default values for missing fields and structured
error reporting when the AI output deviates from the expected schema.

Usage:
    from src.schemas.ai_response import parse_ai_response
    validated = parse_ai_response(raw_json_string)
    # validated is a DashboardResponse with guaranteed field access
"""

import logging
from typing import Any, Dict, List, Optional

from pydantic import BaseModel, Field, field_validator

logger = logging.getLogger(__name__)


# ============================================================
# Dashboard sub-models
# ============================================================

class PositionAdvice(BaseModel):
    """Position advice for holders vs non-holders."""
    no_position: str = Field(default="暂无建议", description="Advice for those without a position")
    has_position: str = Field(default="暂无建议", description="Advice for those with a position")


class CoreConclusion(BaseModel):
    """Core conclusion block of the decision dashboard."""
    one_sentence: str = Field(default="暂无结论", description="One-sentence conclusion (<=30 chars)")
    signal_type: str = Field(default="🟡持有观望", description="Signal icon + label")
    time_sensitivity: str = Field(default="不急", description="Urgency level")
    position_advice: PositionAdvice = Field(default_factory=PositionAdvice)


class TrendStatus(BaseModel):
    """MA trend status."""
    ma_alignment: str = Field(default="", description="MA alignment description")
    is_bullish: bool = Field(default=False, description="Whether trend is bullish")
    trend_score: int = Field(default=50, ge=0, le=100, description="Trend strength score 0-100")


class PricePosition(BaseModel):
    """Current price relative to MAs."""
    current_price: Optional[float] = Field(default=None, description="Current stock price")
    ma5: Optional[float] = None
    ma10: Optional[float] = None
    ma20: Optional[float] = None
    bias_ma5: Optional[float] = Field(default=None, description="BIAS(5) percentage")
    bias_status: str = Field(default="未知", description="safe/warning/danger")
    support_level: Optional[float] = Field(default=None, description="Support price level")
    resistance_level: Optional[float] = Field(default=None, description="Resistance price level")


class VolumeAnalysis(BaseModel):
    """Volume analysis block."""
    volume_ratio: Optional[float] = Field(default=None, description="Volume ratio vs 5d avg")
    volume_status: str = Field(default="平量", description="heavy/light/normal")
    turnover_rate: Optional[float] = Field(default=None, description="Turnover rate %")
    volume_meaning: str = Field(default="", description="Interpretation of volume")


class ChipStructure(BaseModel):
    """Chip distribution analysis."""
    profit_ratio: Optional[float] = Field(default=None, description="Profit ratio")
    avg_cost: Optional[float] = Field(default=None, description="Average cost")
    concentration: Optional[float] = Field(default=None, description="Chip concentration")
    chip_health: str = Field(default="未知", description="healthy/normal/warning")


class DataPerspective(BaseModel):
    """Data-driven analysis block."""
    trend_status: TrendStatus = Field(default_factory=TrendStatus)
    price_position: PricePosition = Field(default_factory=PricePosition)
    volume_analysis: VolumeAnalysis = Field(default_factory=VolumeAnalysis)
    chip_structure: ChipStructure = Field(default_factory=ChipStructure)


class Intelligence(BaseModel):
    """News and sentiment intelligence block."""
    latest_news: str = Field(default="暂无最新消息", description="Latest news summary")
    risk_alerts: List[str] = Field(default_factory=list, description="Risk alert items")
    positive_catalysts: List[str] = Field(default_factory=list, description="Positive catalysts")
    earnings_outlook: str = Field(default="暂无业绩预期", description="Earnings outlook")
    sentiment_summary: str = Field(default="暂无舆情", description="Sentiment one-liner")


class SniperPoints(BaseModel):
    """Precise entry/exit price levels."""
    ideal_buy: str = Field(default="", description="Ideal buy point")
    secondary_buy: str = Field(default="", description="Secondary buy point")
    stop_loss: str = Field(default="", description="Stop loss level")
    take_profit: str = Field(default="", description="Take profit target")


class PositionStrategy(BaseModel):
    """Position sizing and risk control."""
    suggested_position: str = Field(default="建议仓位：0成", description="Suggested position size")
    entry_plan: str = Field(default="", description="Staged entry plan")
    risk_control: str = Field(default="", description="Risk control strategy")


class BattlePlan(BaseModel):
    """Actionable trading plan."""
    sniper_points: SniperPoints = Field(default_factory=SniperPoints)
    position_strategy: PositionStrategy = Field(default_factory=PositionStrategy)
    action_checklist: List[str] = Field(default_factory=list, description="Pre-trade checklist items")


class Dashboard(BaseModel):
    """Complete decision dashboard."""
    core_conclusion: CoreConclusion = Field(default_factory=CoreConclusion)
    data_perspective: DataPerspective = Field(default_factory=DataPerspective)
    intelligence: Intelligence = Field(default_factory=Intelligence)
    battle_plan: BattlePlan = Field(default_factory=BattlePlan)


# ============================================================
# Top-level AI response model
# ============================================================

class DashboardResponse(BaseModel):
    """
    Top-level validated AI response.

    All fields have sensible defaults so partial AI output
    is still usable without KeyError or AttributeError.
    """
    stock_name: str = Field(default="未知", description="Stock Chinese name")
    sentiment_score: int = Field(default=50, ge=0, le=100, description="Overall score 0-100")
    trend_prediction: str = Field(default="震荡", description="Trend prediction label")
    operation_advice: str = Field(default="观望", description="Operation advice label")
    decision_type: str = Field(default="hold", description="buy/hold/sell")
    confidence_level: str = Field(default="中", description="Confidence: 高/中/低")

    dashboard: Dashboard = Field(default_factory=Dashboard)

    # Extended analysis fields
    analysis_summary: str = Field(default="", description="100-char analysis summary")
    key_points: str = Field(default="", description="3-5 key points, comma-separated")
    risk_warning: str = Field(default="", description="Risk warnings")
    buy_reason: str = Field(default="", description="Reason for operation advice")

    trend_analysis: str = Field(default="")
    short_term_outlook: str = Field(default="")
    medium_term_outlook: str = Field(default="")
    technical_analysis: str = Field(default="")
    ma_analysis: str = Field(default="")
    volume_analysis: str = Field(default="")
    pattern_analysis: str = Field(default="")
    fundamental_analysis: str = Field(default="")
    sector_position: str = Field(default="")
    company_highlights: str = Field(default="")
    news_summary: str = Field(default="")
    market_sentiment: str = Field(default="")
    hot_topics: str = Field(default="")

    search_performed: bool = Field(default=False)
    data_sources: str = Field(default="")

    @field_validator("sentiment_score", mode="before")
    @classmethod
    def clamp_score(cls, v: Any) -> int:
        """Clamp sentiment_score to [0, 100] and coerce types."""
        try:
            val = int(v)
        except (TypeError, ValueError):
            return 50
        return max(0, min(100, val))

    @field_validator("decision_type", mode="before")
    @classmethod
    def normalize_decision_type(cls, v: Any) -> str:
        """Normalize decision_type to buy/hold/sell."""
        if not isinstance(v, str):
            return "hold"
        v_lower = v.strip().lower()
        if v_lower in ("buy", "买入", "加仓"):
            return "buy"
        if v_lower in ("sell", "卖出", "减仓"):
            return "sell"
        return "hold"

    def to_legacy_dict(self) -> Dict[str, Any]:
        """
        Convert to the legacy dict format expected by AnalysisResult.

        This bridges the new Pydantic models with existing code that
        expects a plain dict for the 'dashboard' field.
        """
        return {
            "stock_name": self.stock_name,
            "sentiment_score": self.sentiment_score,
            "trend_prediction": self.trend_prediction,
            "operation_advice": self.operation_advice,
            "decision_type": self.decision_type,
            "confidence_level": self.confidence_level,
            "dashboard": self.dashboard.model_dump(),
            "analysis_summary": self.analysis_summary,
            "key_points": self.key_points,
            "risk_warning": self.risk_warning,
            "buy_reason": self.buy_reason,
            "trend_analysis": self.trend_analysis,
            "short_term_outlook": self.short_term_outlook,
            "medium_term_outlook": self.medium_term_outlook,
            "technical_analysis": self.technical_analysis,
            "ma_analysis": self.ma_analysis,
            "volume_analysis": self.volume_analysis,
            "pattern_analysis": self.pattern_analysis,
            "fundamental_analysis": self.fundamental_analysis,
            "sector_position": self.sector_position,
            "company_highlights": self.company_highlights,
            "news_summary": self.news_summary,
            "market_sentiment": self.market_sentiment,
            "hot_topics": self.hot_topics,
            "search_performed": self.search_performed,
            "data_sources": self.data_sources,
        }


# ============================================================
# Parsing entry point
# ============================================================

def parse_ai_response(raw_json: str) -> DashboardResponse:
    """
    Parse and validate raw AI JSON output into a DashboardResponse.

    Uses json_repair for malformed JSON, then Pydantic for validation.
    Fields missing from the AI output receive sensible defaults.

    Args:
        raw_json: Raw JSON string from LLM

    Returns:
        Validated DashboardResponse instance

    Raises:
        Never raises - returns a default DashboardResponse on total failure
    """
    import json
    from json_repair import repair_json

    try:
        # Step 1: Extract JSON from markdown code fences if present
        cleaned = raw_json.strip()
        if cleaned.startswith("```"):
            lines = cleaned.split("\n")
            # Remove first line (```json) and last line (```)
            json_lines = []
            in_block = False
            for line in lines:
                if line.strip().startswith("```") and not in_block:
                    in_block = True
                    continue
                if line.strip() == "```" and in_block:
                    break
                if in_block:
                    json_lines.append(line)
            cleaned = "\n".join(json_lines)

        # Step 2: Repair malformed JSON
        repaired = repair_json(cleaned, return_objects=False)

        # Step 3: Parse JSON
        data = json.loads(repaired)

        # Step 4: Validate with Pydantic
        response = DashboardResponse.model_validate(data)
        logger.debug(f"AI response parsed successfully: score={response.sentiment_score}, "
                     f"advice={response.operation_advice}")
        return response

    except json.JSONDecodeError as e:
        logger.warning(f"JSON decode failed after repair: {e}")
    except Exception as e:
        logger.warning(f"AI response validation failed: {e}")

    # Fallback: return default response
    logger.warning("Returning default DashboardResponse due to parsing failure")
    return DashboardResponse()
