"""Command-line demo for the AI agent starter kit."""

from __future__ import annotations

import argparse
import json
from pathlib import Path

from agent import Agent, OpenAICompatibleBrain, SimpleBrain
from tools.calculator import calculator
from tools.notes import search_notes
from tools.product_docs import search_product_docs
from tools.tickets import create_ticket


ROOT = Path(__file__).parent


def load_profile(mode: str) -> dict:
    profile_path = {
        "personal": ROOT / "profiles" / "personal_companion.json",
        "product": ROOT / "profiles" / "product_copilot.json",
    }.get(mode)

    if profile_path is None:
        raise SystemExit("Mode must be either 'personal' or 'product'.")

    return json.loads(profile_path.read_text(encoding="utf-8"))


def build_agent(mode: str, brain_kind: str = "real", model: str | None = None) -> Agent:
    if brain_kind == "mock":
        brain = SimpleBrain()
    elif brain_kind == "real":
        brain = OpenAICompatibleBrain(model=model)
    else:
        raise ValueError("brain_kind must be 'real' or 'mock'.")

    return Agent(
        profile=load_profile(mode),
        brain=brain,
        tools={
            "search_notes": search_notes,
            "search_product_docs": search_product_docs,
            "calculator": calculator,
            "create_ticket": create_ticket,
        },
    )


def parse_args(argv: list[str] | None = None) -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Run the tiny AI agent demo.")
    parser.add_argument("mode", choices=["personal", "product"], help="Agent profile to use.")
    parser.add_argument("question", nargs="+", help="Question/task for the agent.")
    parser.add_argument(
        "--brain",
        choices=["real", "mock"],
        default="real",
        help="Use a real OpenAI/OpenRouter model or the deterministic offline mock brain.",
    )
    parser.add_argument(
        "--model",
        default=None,
        help="Optional model override, e.g. gpt-4o-mini or openai/gpt-4o-mini.",
    )
    return parser.parse_args(argv)


def main(argv: list[str] | None = None) -> int:
    args = parse_args(argv)
    agent = build_agent(args.mode, brain_kind=args.brain, model=args.model)
    answer = agent.run(" ".join(args.question), verbose=True)
    print(f"\nFinal answer:\n{answer}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
