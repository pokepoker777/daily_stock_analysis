# -*- coding: utf-8 -*-
"""Unit tests for Pydantic AI response validation schemas."""

import json
import unittest

from src.schemas.ai_response import (
    DashboardResponse,
    parse_ai_response,
)


class TestDashboardResponse(unittest.TestCase):
    """Test the DashboardResponse Pydantic model."""

    def test_full_valid_json(self):
        data = {
            "stock_name": "贵州茅台",
            "sentiment_score": 75,
            "trend_prediction": "看多",
            "operation_advice": "买入",
            "decision_type": "buy",
            "confidence_level": "高",
            "dashboard": {
                "core_conclusion": {
                    "one_sentence": "多头排列，建议逢低买入",
                    "signal_type": "🟢买入信号",
                    "time_sensitivity": "本周内",
                    "position_advice": {
                        "no_position": "可小仓介入",
                        "has_position": "继续持有",
                    },
                },
                "data_perspective": {},
                "intelligence": {},
                "battle_plan": {},
            },
            "analysis_summary": "茅台走势良好",
            "search_performed": True,
        }
        resp = DashboardResponse.model_validate(data)
        self.assertEqual(resp.stock_name, "贵州茅台")
        self.assertEqual(resp.sentiment_score, 75)
        self.assertEqual(resp.decision_type, "buy")
        self.assertEqual(resp.dashboard.core_conclusion.one_sentence, "多头排列，建议逢低买入")

    def test_partial_json_gets_defaults(self):
        data = {
            "stock_name": "平安银行",
            "sentiment_score": 45,
            "trend_prediction": "震荡",
            "operation_advice": "观望",
        }
        resp = DashboardResponse.model_validate(data)
        self.assertEqual(resp.decision_type, "hold")  # default
        self.assertEqual(resp.confidence_level, "中")
        self.assertIsNotNone(resp.dashboard)
        self.assertEqual(resp.dashboard.core_conclusion.one_sentence, "暂无结论")

    def test_score_clamping(self):
        resp = DashboardResponse.model_validate({"sentiment_score": 150})
        self.assertEqual(resp.sentiment_score, 100)

        resp2 = DashboardResponse.model_validate({"sentiment_score": -10})
        self.assertEqual(resp2.sentiment_score, 0)

    def test_score_type_coercion(self):
        resp = DashboardResponse.model_validate({"sentiment_score": "72"})
        self.assertEqual(resp.sentiment_score, 72)

        resp2 = DashboardResponse.model_validate({"sentiment_score": "invalid"})
        self.assertEqual(resp2.sentiment_score, 50)  # fallback

    def test_decision_type_normalization(self):
        resp = DashboardResponse.model_validate({"decision_type": "买入"})
        self.assertEqual(resp.decision_type, "buy")

        resp2 = DashboardResponse.model_validate({"decision_type": "SELL"})
        self.assertEqual(resp2.decision_type, "sell")

        resp3 = DashboardResponse.model_validate({"decision_type": "unknown"})
        self.assertEqual(resp3.decision_type, "hold")

    def test_to_legacy_dict(self):
        resp = DashboardResponse.model_validate({
            "stock_name": "Test",
            "sentiment_score": 60,
        })
        d = resp.to_legacy_dict()
        self.assertIsInstance(d, dict)
        self.assertEqual(d["stock_name"], "Test")
        self.assertEqual(d["sentiment_score"], 60)
        self.assertIsInstance(d["dashboard"], dict)


class TestParseAiResponse(unittest.TestCase):
    """Test the parse_ai_response entry point."""

    def test_clean_json(self):
        raw = json.dumps({
            "stock_name": "比亚迪",
            "sentiment_score": 80,
            "trend_prediction": "强烈看多",
            "operation_advice": "买入",
        })
        resp = parse_ai_response(raw)
        self.assertEqual(resp.stock_name, "比亚迪")
        self.assertEqual(resp.sentiment_score, 80)

    def test_json_in_code_fences(self):
        raw = '```json\n{"stock_name":"宁德时代","sentiment_score":65}\n```'
        resp = parse_ai_response(raw)
        self.assertEqual(resp.stock_name, "宁德时代")
        self.assertEqual(resp.sentiment_score, 65)

    def test_malformed_json_returns_default(self):
        raw = "This is not JSON at all"
        resp = parse_ai_response(raw)
        self.assertEqual(resp.stock_name, "未知")
        self.assertEqual(resp.sentiment_score, 50)

    def test_trailing_comma_repair(self):
        raw = '{"stock_name":"Test","sentiment_score":55,}'
        resp = parse_ai_response(raw)
        self.assertEqual(resp.stock_name, "Test")
        self.assertEqual(resp.sentiment_score, 55)

    def test_empty_string(self):
        resp = parse_ai_response("")
        self.assertEqual(resp.sentiment_score, 50)
        self.assertFalse(resp.search_performed)


if __name__ == "__main__":
    unittest.main()
