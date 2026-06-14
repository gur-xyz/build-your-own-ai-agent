"""Personal-memory search tool."""

from __future__ import annotations

from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
NOTES_PATH = ROOT / "data" / "personal_notes.txt"


def search_notes(args: dict) -> dict:
    query = str(args.get("query", "")).lower()
    text = NOTES_PATH.read_text(encoding="utf-8")
    lines = [line.strip() for line in text.splitlines() if line.strip()]

    matches = [line for line in lines if any(word in line.lower() for word in query.split())]
    if not matches:
        matches = lines[:2]

    return {
        "ok": True,
        "matches": matches[:3],
        "summary": " | ".join(matches[:2]),
    }
