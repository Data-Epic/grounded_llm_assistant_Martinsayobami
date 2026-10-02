import csv
import json

import pytest


@pytest.fixture
def sample_csv(tmp_path):
    path = tmp_path / "mock.csv"
    rows = [
        {"customer_id": "C001", "name": "Amaka Okafor", "country": "Nigeria",
         "loyalty_score": "88", "signup_date": "2023-01-14", "total_spend": "542.30"},
        {"customer_id": "C002", "name": "Tunde Bello", "country": "Nigeria",
         "loyalty_score": "45", "signup_date": "2023-03-02", "total_spend": "120.00"},
        {"customer_id": "C005", "name": "Sarah Johnson", "country": "USA",
         "loyalty_score": "91", "signup_date": "2021-09-05", "total_spend": "980.20"},
        {"customer_id": "C006", "name": "Mike Davis", "country": "USA",
         "loyalty_score": "55", "signup_date": "2022-02-17", "total_spend": "410.00"},
    ]
    with open(path, "w", newline="") as f:
        writer = csv.DictWriter(f, fieldnames=rows[0].keys())
        writer.writeheader()
        writer.writerows(rows)
    return str(path)


def make_groq_response(content: str, prompt_tokens=100, completion_tokens=20):
    return {
        "choices": [{"message": {"content": content}}],
        "usage": {"prompt_tokens": prompt_tokens, "completion_tokens": completion_tokens},
    }


@pytest.fixture
def valid_json_content():
    return json.dumps(
        {"answer": "Amaka Okafor has the highest loyalty score in Nigeria.",
         "source_rows": ["C001"], "confidence": "high"}
    )


@pytest.fixture
def not_in_data_content():
    return json.dumps({"answer": "NOT_IN_DATA", "source_rows": [], "confidence": "high"})
