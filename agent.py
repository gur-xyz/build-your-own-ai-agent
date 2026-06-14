"""A tiny AI-agent loop, built for teaching.

The default path can call any OpenAI-compatible chat-completions endpoint
(OpenAI or OpenRouter). A deterministic `SimpleBrain` remains available for
tests and offline demos.
"""

from __future__ import annotations

import json
import os
import re
import urllib.error
import urllib.request
from dataclasses import dataclass, field
from typing import Any, Callable, Protocol


Message = dict[str, Any]
Tool = Callable[[dict[str, Any]], dict[str, Any]]


class Brain(Protocol):
    """Something that can decide the next agent step."""

    def decide(self, messages: list[Message], profile: dict[str, Any]) -> "Decision":
        """Return either a tool decision or a final-answer decision."""


@dataclass
class Decision:
    """What the brain wants to do next."""

    kind: str  # "tool" or "final"
    content: str = ""
    tool_name: str = ""
    tool_args: dict[str, Any] = field(default_factory=dict)
    reason: str = ""


@dataclass
class SimpleBrain:
    """A deterministic offline brain used for tests and demos without an API key."""

    def decide(self, messages: list[Message], profile: dict[str, Any]) -> Decision:
        user_text = messages[0]["content"].lower()
        mode = profile.get("mode", "personal")

        if mode == "product":
            return self._decide_product(user_text, messages)
        return self._decide_personal(user_text, messages)

    def _decide_personal(self, user_text: str, messages: list[Message]) -> Decision:
        if not has_tool_result(messages, "search_notes"):
            return Decision(
                kind="tool",
                tool_name="search_notes",
                tool_args={"query": user_text},
                reason="I should check the user's notes before giving personal advice.",
            )

        notes = last_tool_result(messages, "search_notes")

        if any(word in user_text for word in ["calculate", "math", "cost", "+", "-"]):
            if not has_tool_result(messages, "calculator"):
                return Decision(
                    kind="tool",
                    tool_name="calculator",
                    tool_args={"expression": "2 + 2"},
                    reason="The user asked something math-like, so I should calculate instead of guessing.",
                )

        return Decision(
            kind="final",
            content=(
                "Here is the simple plan: focus on one useful build, explain it clearly, "
                "and turn the result into content. I checked your notes and found: "
                f"{notes.get('summary', 'no matching note')}"
            ),
        )

    def _decide_product(self, user_text: str, messages: list[Message]) -> Decision:
        wants_human = any(word in user_text for word in ["human", "angry", "failed", "broken", "urgent"])

        if not has_tool_result(messages, "search_product_docs"):
            return Decision(
                kind="tool",
                tool_name="search_product_docs",
                tool_args={"query": user_text},
                reason="A support agent should check product docs before answering.",
            )

        docs = last_tool_result(messages, "search_product_docs")

        if wants_human and not has_tool_result(messages, "create_ticket"):
            return Decision(
                kind="tool",
                tool_name="create_ticket",
                tool_args={
                    "title": "Customer needs human help",
                    "summary": messages[0]["content"],
                },
                reason="The user is asking for a human or has a serious problem, so escalate.",
            )

        if has_tool_result(messages, "create_ticket"):
            ticket = last_tool_result(messages, "create_ticket")
            return Decision(
                kind="final",
                content=(
                    "I found the docs, but this needs a human. "
                    f"I created support ticket {ticket['ticket_id']}."
                ),
            )

        return Decision(
            kind="final",
            content=(
                "Based on the product docs: "
                f"{docs.get('answer', 'I could not find a confident answer. Please contact support.')}"
            ),
        )


@dataclass
class OpenAICompatibleBrain:
    """Real model brain using the OpenAI-compatible chat completions API.

    Works with OpenAI:

        export OPENAI_API_KEY=...
        export AGENT_MODEL="gpt-4o-mini"

    Works with OpenRouter:

        export OPENROUTER_API_KEY=...
        export AGENT_MODEL="openai/gpt-4o-mini"

    No external Python package is required; this uses the standard library.
    """

    api_key: str | None = None
    model: str | None = None
    base_url: str | None = None
    temperature: float = 0.2

    def __post_init__(self) -> None:
        self.api_key = self.api_key or os.getenv("OPENROUTER_API_KEY") or os.getenv("OPENAI_API_KEY")
        self.base_url = self.base_url or self._default_base_url()
        self.model = self.model or os.getenv("AGENT_MODEL") or self._default_model()

        if not self.api_key:
            raise RuntimeError(
                "Missing API key. Set OPENROUTER_API_KEY or OPENAI_API_KEY, "
                "or run with '--brain mock' for the offline demo."
            )

    def decide(self, messages: list[Message], profile: dict[str, Any]) -> Decision:
        response_text = self._chat(messages, profile)
        payload = _parse_json_object(response_text)
        return _decision_from_payload(payload)

    def _default_base_url(self) -> str:
        if os.getenv("OPENROUTER_API_KEY"):
            return os.getenv("OPENROUTER_BASE_URL", "https://openrouter.ai/api/v1")
        return os.getenv("OPENAI_BASE_URL", "https://api.openai.com/v1")

    def _default_model(self) -> str:
        if os.getenv("OPENROUTER_API_KEY"):
            return "openai/gpt-4o-mini"
        return "gpt-4o-mini"

    def _chat(self, messages: list[Message], profile: dict[str, Any]) -> str:
        body = {
            "model": self.model,
            "messages": [
                {"role": "system", "content": _system_prompt(profile)},
                {"role": "user", "content": _format_agent_state(messages)},
            ],
            "temperature": self.temperature,
            "response_format": {"type": "json_object"},
        }

        request = urllib.request.Request(
            url=f"{self.base_url.rstrip('/')}/chat/completions",
            data=json.dumps(body).encode("utf-8"),
            headers={
                "Authorization": f"Bearer {self.api_key}",
                "Content-Type": "application/json",
                "HTTP-Referer": "https://github.com/gur-xyz/build-your-own-ai-agent",
                "X-Title": "Build Your Own AI Agent Starter Kit",
            },
            method="POST",
        )

        try:
            with urllib.request.urlopen(request, timeout=60) as response:
                data = json.loads(response.read().decode("utf-8"))
        except urllib.error.HTTPError as exc:
            error_body = exc.read().decode("utf-8", errors="replace")[:500]
            raise RuntimeError(f"Model API error {exc.code}: {error_body}") from exc

        return data["choices"][0]["message"]["content"]


@dataclass
class Agent:
    """Minimal agent: profile + brain + tools + loop."""

    profile: dict[str, Any]
    brain: Brain
    tools: dict[str, Tool]
    max_steps: int = 5

    def run(self, user_text: str, verbose: bool = True) -> str:
        messages: list[Message] = [
            {"role": "user", "content": user_text},
        ]

        if verbose:
            print(f"Agent name: {self.profile.get('name', 'Agent')}")
            print(f"Agent job: {self.profile.get('job', 'Help the user')}")
            print(f"User: {user_text}")

        for step in range(1, self.max_steps + 1):
            decision = self.brain.decide(messages, self.profile)

            if verbose:
                print(f"\nStep {step}: brain decides")
                print(f"Reason: {decision.reason or 'Ready to answer.'}")

            if decision.kind == "final":
                if verbose:
                    print("Action: final answer")
                return decision.content

            if decision.kind != "tool":
                raise ValueError(f"Unknown decision kind: {decision.kind}")

            tool = self.tools.get(decision.tool_name)
            if tool is None:
                raise ValueError(f"Unknown tool: {decision.tool_name}")

            if verbose:
                print(f"Action: use tool `{decision.tool_name}`")
                print(f"Tool input: {decision.tool_args}")

            result = tool(decision.tool_args)

            if verbose:
                print(f"Tool result: {result}")

            messages.append(
                {
                    "role": "assistant",
                    "type": "tool_call",
                    "tool": decision.tool_name,
                    "args": decision.tool_args,
                }
            )
            messages.append(
                {
                    "role": "tool",
                    "tool": decision.tool_name,
                    "content": result,
                }
            )

        raise RuntimeError("Agent reached max_steps without a final answer.")


def has_tool_result(messages: list[Message], tool_name: str) -> bool:
    return any(message.get("role") == "tool" and message.get("tool") == tool_name for message in messages)


def last_tool_result(messages: list[Message], tool_name: str) -> dict[str, Any]:
    for message in reversed(messages):
        if message.get("role") == "tool" and message.get("tool") == tool_name:
            content = message.get("content", {})
            return content if isinstance(content, dict) else {"value": content}
    return {}


def _system_prompt(profile: dict[str, Any]) -> str:
    return f"""
You are the decision-making brain inside a small AI agent.

Agent profile:
{json.dumps(profile, indent=2)}

You must choose exactly one next step.

Available tools:
- search_notes: search local personal notes. Args: {{"query": "..."}}
- search_product_docs: search product documentation. Args: {{"query": "..."}}
- calculator: calculate basic arithmetic. Args: {{"expression": "2 + 2"}}
- create_ticket: create a support handoff ticket. Args: {{"title": "...", "summary": "..."}}

Return only valid JSON. Do not return markdown.

For tool use:
{{
  "kind": "tool",
  "tool_name": "search_product_docs",
  "tool_args": {{"query": "refund policy"}},
  "reason": "I should check the product docs before answering."
}}

For a final answer:
{{
  "kind": "final",
  "content": "Your answer here.",
  "reason": "I have enough information to answer."
}}

Rules:
- Use tools when the answer depends on notes, product docs, arithmetic, or handoff.
- Do not invent product policy; search product docs first.
- If the user asks for a human, or the issue involves payment failure, create a ticket.
- If a relevant tool result is already present, use it instead of calling the same tool again.
""".strip()


def _format_agent_state(messages: list[Message]) -> str:
    return "Current conversation/tool state:\n" + json.dumps(messages, indent=2, ensure_ascii=False)


def _parse_json_object(text: str) -> dict[str, Any]:
    cleaned = text.strip()
    cleaned = re.sub(r"^```(?:json)?\s*", "", cleaned)
    cleaned = re.sub(r"\s*```$", "", cleaned)
    try:
        payload = json.loads(cleaned)
    except json.JSONDecodeError as exc:
        raise ValueError(f"Model did not return valid JSON: {text}") from exc
    if not isinstance(payload, dict):
        raise ValueError(f"Model JSON must be an object: {payload}")
    return payload


def _decision_from_payload(payload: dict[str, Any]) -> Decision:
    kind = str(payload.get("kind", ""))
    if kind == "final":
        return Decision(
            kind="final",
            content=str(payload.get("content", "")),
            reason=str(payload.get("reason", "")),
        )
    if kind == "tool":
        tool_args = payload.get("tool_args", {})
        if not isinstance(tool_args, dict):
            raise ValueError("tool_args must be a JSON object")
        return Decision(
            kind="tool",
            tool_name=str(payload.get("tool_name", "")),
            tool_args=tool_args,
            reason=str(payload.get("reason", "")),
        )
    raise ValueError(f"Unknown model decision kind: {payload}")
