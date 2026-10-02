"""Parsing and validation for the structured JSON the model must return.

Expected shape:
{
    "answer": "<string>",
    "source_rows": ["<customer_id>", ...],   # list, may be empty
    "confidence": "high" | "medium" | "low"
}
"""
from __future__ import annotations

import json
from dataclasses import dataclass

from .exceptions import ResponseParsingError

ALLOWED_CONFIDENCE = {"high", "medium", "low"}
REQUIRED_FIELDS = ("answer", "source_rows", "confidence")


@dataclass
class GroundedAnswer:
    answer: str
    source_rows: list
    confidence: str


def parse_model_content(raw_content: str) -> GroundedAnswer:
    """Parse and validate the raw string content returned by the model.

    Raises ResponseParsingError (never lets a bad response crash the caller)
    if the content is not valid JSON or does not match the expected schema.
    """
    if raw_content is None:
        raise ResponseParsingError("Model returned empty content.")

    cleaned = raw_content.strip()
    # Models sometimes wrap JSON in markdown fences despite instructions.
    if cleaned.startswith("```"):
        cleaned = cleaned.strip("`")
        if cleaned.lower().startswith("json"):
            cleaned = cleaned[4:]
        cleaned = cleaned.strip()

    try:
        data = json.loads(cleaned)
    except json.JSONDecodeError as exc:
        raise ResponseParsingError(f"Model content is not valid JSON: {exc}") from exc

    if not isinstance(data, dict):
        raise ResponseParsingError("Model JSON is not an object.")

    missing = [f for f in REQUIRED_FIELDS if f not in data]
    if missing:
        raise ResponseParsingError(f"Missing required field(s): {missing}")

    answer = data["answer"]
    source_rows = data["source_rows"]
    confidence = data["confidence"]

    if not isinstance(answer, str):
        raise ResponseParsingError("'answer' must be a string.")
    if not isinstance(source_rows, list):
        raise ResponseParsingError("'source_rows' must be a list.")
    if not isinstance(confidence, str) or confidence.lower() not in ALLOWED_CONFIDENCE:
        raise ResponseParsingError(
            f"'confidence' must be one of {ALLOWED_CONFIDENCE}, got {confidence!r}."
        )

    return GroundedAnswer(answer=answer, source_rows=source_rows, confidence=confidence.lower())
