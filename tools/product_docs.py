"""Product documentation search tool."""

from __future__ import annotations

from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
DOCS_PATH = ROOT / "data" / "product_docs.txt"


def search_product_docs(args: dict) -> dict:
    query = str(args.get("query", "")).lower()
    docs = DOCS_PATH.read_text(encoding="utf-8")
    sections = [section.strip() for section in docs.split("\n\n") if section.strip()]

    scored: list[tuple[int, str]] = []
    for section in sections:
        score = sum(1 for word in query.split() if word in section.lower())
        scored.append((score, section))

    scored.sort(reverse=True, key=lambda item: item[0])
    best_score, best_section = scored[0]

    if best_score == 0:
        return {
            "ok": False,
            "answer": "I could not find this in the product docs.",
            "matched_section": "",
        }

    return {
        "ok": True,
        "answer": best_section.replace("\n", " "),
        "matched_section": best_section,
    }
