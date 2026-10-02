from unittest.mock import MagicMock, patch

import pytest

from groundedqa.client import GroqClient
from groundedqa.exceptions import GroqClientError, GroqRateLimitError, GroqServerError
from groundedqa.schema import GroundedAnswer
from groundedqa import token_tracker


@pytest.fixture(autouse=True)
def reset_tracker():
    token_tracker.tracker.prompt_tokens = 0
    token_tracker.tracker.completion_tokens = 0
    token_tracker.tracker.calls = 0
    yield


def _mock_response(status_code, json_body=None, text=""):
    resp = MagicMock()
    resp.status_code = status_code
    resp.json.return_value = json_body or {}
    resp.text = text
    return resp


def test_client_requires_api_key(monkeypatch):
    monkeypatch.delenv("GROQ_API_KEY", raising=False)
    with patch("groundedqa.client.load_dotenv"):
        with pytest.raises(ValueError):
            GroqClient(api_key=None)


def test_chat_completion_success(valid_json_content):
    client = GroqClient(api_key="test-key")
    body = {
        "choices": [{"message": {"content": valid_json_content}}],
        "usage": {"prompt_tokens": 50, "completion_tokens": 10},
    }
    with patch("groundedqa.client.requests.post", return_value=_mock_response(200, body)):
        result = client.chat_completion([{"role": "user", "content": "hi"}])
    assert result["usage"]["prompt_tokens"] == 50


def test_chat_completion_401_raises():
    client = GroqClient(api_key="bad-key")
    with patch(
        "groundedqa.client.requests.post",
        return_value=_mock_response(401, text="unauthorized"),
    ):
        with pytest.raises(GroqClientError):
            client.chat_completion([{"role": "user", "content": "hi"}])


def test_chat_completion_5xx_raises():
    client = GroqClient(api_key="test-key")
    with patch(
        "groundedqa.client.requests.post",
        return_value=_mock_response(500, text="server exploded"),
    ):
        with pytest.raises(GroqServerError):
            client.chat_completion([{"role": "user", "content": "hi"}])


def test_chat_completion_429_then_success(valid_json_content):
    client = GroqClient(api_key="test-key")
    success_body = {
        "choices": [{"message": {"content": valid_json_content}}],
        "usage": {"prompt_tokens": 10, "completion_tokens": 5},
    }
    responses = [
        _mock_response(429, text="rate limited"),
        _mock_response(200, success_body),
    ]
    with patch("groundedqa.client.requests.post", side_effect=responses), patch(
        "groundedqa.client.time.sleep"
    ):
        result = client.chat_completion([{"role": "user", "content": "hi"}])
    assert result["usage"]["prompt_tokens"] == 10


def test_chat_completion_429_exceeds_retries():
    client = GroqClient(api_key="test-key")
    responses = [_mock_response(429, text="rate limited")] * 10
    with patch("groundedqa.client.requests.post", side_effect=responses), patch(
        "groundedqa.client.time.sleep"
    ):
        with pytest.raises(GroqRateLimitError):
            client.chat_completion([{"role": "user", "content": "hi"}])


def test_ask_returns_grounded_answer(sample_csv, valid_json_content):
    client = GroqClient(api_key="test-key")
    body = {
        "choices": [{"message": {"content": valid_json_content}}],
        "usage": {"prompt_tokens": 30, "completion_tokens": 8},
    }
    with patch("groundedqa.client.requests.post", return_value=_mock_response(200, body)):
        result = client.ask("Who is in Nigeria?", sample_csv)
    assert isinstance(result, GroundedAnswer)
    assert token_tracker.tracker.calls == 1
    assert token_tracker.tracker.prompt_tokens == 30


def test_ask_not_in_data_path(sample_csv, not_in_data_content):
    client = GroqClient(api_key="test-key")
    body = {
        "choices": [{"message": {"content": not_in_data_content}}],
        "usage": {"prompt_tokens": 15, "completion_tokens": 5},
    }
    with patch("groundedqa.client.requests.post", return_value=_mock_response(200, body)):
        result = client.ask("What is the capital of Mars?", sample_csv)
    assert isinstance(result, GroundedAnswer)
    assert result.answer == "NOT_IN_DATA"


def test_ask_handles_non_json_gracefully(sample_csv):
    client = GroqClient(api_key="test-key")
    body = {
        "choices": [{"message": {"content": "I refuse to speak JSON today."}}],
        "usage": {"prompt_tokens": 15, "completion_tokens": 5},
    }
    with patch("groundedqa.client.requests.post", return_value=_mock_response(200, body)):
        result = client.ask("Who is in Nigeria?", sample_csv)
    assert isinstance(result, dict)
    assert result["error"] == "unparsable_response"
