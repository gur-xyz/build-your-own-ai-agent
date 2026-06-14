"""Fake escalation tool.

A real product agent would call Intercom, Zendesk, Linear, or Jira here.
"""

from __future__ import annotations

import hashlib


def create_ticket(args: dict) -> dict:
    title = str(args.get("title", "Support request"))
    summary = str(args.get("summary", ""))
    ticket_hash = hashlib.sha1(f"{title}:{summary}".encode("utf-8")).hexdigest()[:8]
    return {
        "ok": True,
        "ticket_id": f"DEMO-{ticket_hash}",
        "title": title,
        "summary": summary,
        "note": "Demo only: no real ticket was created.",
    }
