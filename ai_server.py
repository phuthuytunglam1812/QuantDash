"""Small server-side AI proxy for QuantDash.

The browser never receives OPENAI_API_KEY. Keep the key in the project .env.
"""

from __future__ import annotations

import json
import os
from typing import Any

import requests
from dotenv import load_dotenv
from starlette.applications import Starlette
from starlette.requests import Request
from starlette.responses import JSONResponse
from starlette.routing import Route

load_dotenv()


def _output_text(payload: dict[str, Any]) -> str:
    parts: list[str] = []
    for item in payload.get("output", []):
        for content in item.get("content", []):
            if content.get("type") == "output_text" and content.get("text"):
                parts.append(content["text"])
    return "\n".join(parts).strip()


def _ask(instructions: str, user_input: str) -> str:
    api_key = os.getenv("OPENAI_API_KEY")
    if not api_key:
        raise RuntimeError("OPENAI_API_KEY is not configured")
    response = requests.post(
        "https://api.openai.com/v1/responses",
        headers={"Authorization": f"Bearer {api_key}", "Content-Type": "application/json"},
        json={
            "model": os.getenv("OPENAI_MODEL", "gpt-4.1-mini"),
            "instructions": instructions,
            "input": user_input,
            "max_output_tokens": 450,
            "store": False,
        },
        timeout=35,
    )
    response.raise_for_status()
    text = _output_text(response.json())
    if not text:
        raise RuntimeError("OpenAI returned no output text")
    return text


async def health(_: Request) -> JSONResponse:
    return JSONResponse({"ok": True, "ai_configured": bool(os.getenv("OPENAI_API_KEY"))})


async def intent_advice(request: Request) -> JSONResponse:
    body = await request.json()
    intent = str(body.get("intent", "")).strip()[:1200]
    if not intent:
        return JSONResponse({"error": "intent is required"}, status_code=400)
    try:
        guidance = _ask(
            "You are QuantDash's beginner investment-research coach. Respond in 90-140 plain-English words. "
            "Translate the user's goal into a research checklist using only these available concepts: 1M/3M/6M momentum, "
            "YoY revenue growth, profit margin, positive P/E, RSI, beta, volatility, drawdown, composite score and SPY comparison. "
            "Explain unfamiliar terms briefly. Never recommend buying or selling, promise returns, or imply suitability. "
            "Explicitly state one dataset limitation relevant to the request.",
            intent,
        )
        return JSONResponse({"guidance": guidance})
    except Exception as exc:
        return JSONResponse({"error": "AI guidance unavailable", "detail": str(exc)[:180]}, status_code=503)


async def market_feedback(request: Request) -> JSONResponse:
    body = await request.json()
    compact = json.dumps(body, separators=(",", ":"))[:7000]
    try:
        raw = _ask(
            "You are a beginner-friendly coach reviewing a fictional five-day investing simulation. "
            "Return ONLY valid JSON with four string keys: did_well, review_next, bias_check, next_action. "
            "Use the actual positions, contribution and goal supplied. If there is only one holding, discuss concentration; "
            "do not invent a negative contributor when none exists. Explain that one-day profit/loss does not validate the decision, "
            "and that simulated moves combine a seeded market regime, score tilt and volatility-scaled shock—not live prices or forecasts. "
            "Each value must be 1-2 concise, non-advisory sentences in plain English.",
            compact,
        )
        parsed = json.loads(raw.removeprefix("```json").removesuffix("```").strip())
        required = ("did_well", "review_next", "bias_check", "next_action")
        if not all(isinstance(parsed.get(key), str) for key in required):
            raise ValueError("AI response did not match the feedback schema")
        return JSONResponse({key: parsed[key] for key in required})
    except Exception as exc:
        return JSONResponse({"error": "AI feedback unavailable", "detail": str(exc)[:180]}, status_code=503)


app = Starlette(
    debug=False,
    routes=[
        Route("/api/health", health, methods=["GET"]),
        Route("/api/intent-advice", intent_advice, methods=["POST"]),
        Route("/api/market-feedback", market_feedback, methods=["POST"]),
    ],
)

