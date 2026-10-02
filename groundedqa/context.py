"""Selects only the rows relevant to a question instead of sending a whole CSV.

Strategy (kept simple and explainable for the report):
1. Look for a known country name mentioned in the question -> filter to that country.
2. Look for a loyalty-score comparison ("above/over/greater than X",
   "below/under/less than X") -> filter numerically.
3. If neither matches, fall back to a small default sample (first N rows) so we
   never silently send the entire dataset.
"""
from __future__ import annotations

import csv
import re
from pathlib import Path

DEFAULT_SAMPLE_SIZE = 5

_THRESHOLD_PATTERNS = [
    (re.compile(r"(?:above|over|greater than|more than)\s+(\d+)", re.I), "gt"),
    (re.compile(r"(?:below|under|less than|lower than)\s+(\d+)", re.I), "lt"),
    (re.compile(r"(?:at least|>=)\s*(\d+)", re.I), "gte"),
    (re.compile(r"(?:at most|<=)\s*(\d+)", re.I), "lte"),
]


def load_rows(csv_path: str | Path) -> list[dict]:
    with open(csv_path, newline="", encoding="utf-8") as f:
        return list(csv.DictReader(f))


def _known_countries(rows: list[dict]) -> set:
    return {row["country"] for row in rows if row.get("country")}


def _find_country(question: str, countries: set) -> str | None:
    q_lower = question.lower()
    for country in countries:
        if country.lower() in q_lower:
            return country
    return None


def _find_threshold(question: str):
    for pattern, op in _THRESHOLD_PATTERNS:
        match = pattern.search(question)
        if match:
            return op, int(match.group(1))
    return None, None


def select_relevant_rows(question: str, rows: list[dict]) -> list[dict]:
    """Return the subset of rows relevant to `question`.

    Never returns the full dataset unless the dataset is already <= the
    default sample size.
    """
    if not rows:
        return []

    countries = _known_countries(rows)
    country = _find_country(question, countries)
    op, threshold = _find_threshold(question)

    filtered = rows
    matched_any_filter = False

    if country:
        filtered = [r for r in filtered if r.get("country") == country]
        matched_any_filter = True

    if op and threshold is not None:
        def keep(r):
            try:
                score = float(r.get("loyalty_score", ""))
            except (TypeError, ValueError):
                return False
            if op == "gt":
                return score > threshold
            if op == "lt":
                return score < threshold
            if op == "gte":
                return score >= threshold
            if op == "lte":
                return score <= threshold
            return False

        filtered = [r for r in filtered if keep(r)]
        matched_any_filter = True

    if not matched_any_filter:
        return rows[:DEFAULT_SAMPLE_SIZE]

    return filtered


def rows_to_prompt_block(rows: list[dict]) -> str:
    """Render selected rows as a compact, labelled text block for the prompt."""
    if not rows:
        return "(no matching rows found)"
    header = ", ".join(rows[0].keys())
    lines = [header]
    for r in rows:
        lines.append(", ".join(str(v) for v in r.values()))
    return "\n".join(lines)
