from __future__ import annotations

import unittest

from agent import _decision_from_payload, _parse_json_object
from main import build_agent
from tools.calculator import calculator


class AgentStarterKitTests(unittest.TestCase):
    def test_personal_agent_returns_personal_plan(self) -> None:
        agent = build_agent("personal", brain_kind="mock")
        answer = agent.run("What should I focus on today?", verbose=False)
        self.assertIn("focus on one useful build", answer)

    def test_product_agent_answers_refund_question(self) -> None:
        agent = build_agent("product", brain_kind="mock")
        answer = agent.run("How do refunds work?", verbose=False)
        self.assertIn("14 days", answer)

    def test_product_agent_escalates_to_human(self) -> None:
        agent = build_agent("product", brain_kind="mock")
        answer = agent.run("My payment failed and I need a human", verbose=False)
        self.assertIn("DEMO-", answer)

    def test_calculator_blocks_code_execution(self) -> None:
        result = calculator({"expression": "__import__('os').system('echo bad')"})
        self.assertFalse(result["ok"])

    def test_model_json_can_be_parsed_from_code_fence(self) -> None:
        payload = _parse_json_object('```json\n{"kind":"final","content":"done"}\n```')
        decision = _decision_from_payload(payload)
        self.assertEqual(decision.kind, "final")
        self.assertEqual(decision.content, "done")


if __name__ == "__main__":
    unittest.main()
