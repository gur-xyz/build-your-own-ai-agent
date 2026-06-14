"""A tiny safe calculator tool for demo purposes."""

from __future__ import annotations

import ast
import operator
from typing import Any


OPS = {
    ast.Add: operator.add,
    ast.Sub: operator.sub,
    ast.Mult: operator.mul,
    ast.Div: operator.truediv,
    ast.USub: operator.neg,
}


def calculator(args: dict) -> dict:
    expression = str(args.get("expression", ""))
    try:
        result = _eval(ast.parse(expression, mode="eval").body)
    except Exception as exc:  # intentionally returned as data for the agent
        return {"ok": False, "expression": expression, "error": str(exc)}
    return {"ok": True, "expression": expression, "result": result}


def _eval(node: ast.AST) -> Any:
    if isinstance(node, ast.Constant) and isinstance(node.value, (int, float)):
        return node.value
    if isinstance(node, ast.BinOp) and type(node.op) in OPS:
        return OPS[type(node.op)](_eval(node.left), _eval(node.right))
    if isinstance(node, ast.UnaryOp) and type(node.op) in OPS:
        return OPS[type(node.op)](_eval(node.operand))
    raise ValueError("Only basic arithmetic is allowed.")
