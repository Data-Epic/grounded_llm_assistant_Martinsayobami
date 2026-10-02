"""GroqClient: talks to the Groq chat completions endpoint via `requests`."""
from __future__ import annotations

import os
import time

import requests
from dotenv import load_dotenv

from . import prompts
from .context import load_rows, rows_to_prompt_block, select_relevant_rows
from .exceptions import (
    GroqClientError,
    GroqRateLimitError,
    GroqServerError,
    ResponseParsingError,
)
from .schema import GroundedAnswer, parse_model_content
from .token_tracker import tracker

GROQ_URL = "https://api.groq.com/openai/v1/chat/completions"
DEFAULT_MODEL = "openai/gpt-oss-20b" 
MAX_RETRIES = 3
BACKOFF_SECONDS = 1


class GroqClient:
    def __init__(self, api_key: str | None = None, model: str = DEFAULT_MODEL):
        if api_key is None:
            load_dotenv()
            api_key = os.getenv("GROQ_API_KEY")
        if not api_key:
            raise ValueError(
                "No Groq API key found. Set GROQ_API_KEY in your .env file."
            )
        self.api_key = api_key
        self.model = model

    def _headers(self) -> dict:
        return {
            "Authorization": f"Bearer {self.api_key}",
            "Content-Type": "application/json",
        }

    def chat_completion(
        self, messages: list[dict], temperature: float = 0.0, max_tokens: int = 500
    ) -> dict:
        """POST to the Groq chat completions endpoint with 429 retry/backoff.

        Raises GroqClientError / GroqServerError / GroqRateLimitError on failure.
        Returns the parsed JSON response body on success.
        """
        payload = {
            "model": self.model,
            "messages": messages,
            "temperature": temperature,
            "max_tokens": max_tokens,
        }

        attempt = 0
        while True:
            response = requests.post(GROQ_URL, json=payload, headers=self._headers())

            if response.status_code == 200:
                return response.json()

            if response.status_code == 429:
                attempt += 1
                if attempt > MAX_RETRIES:
                    raise GroqRateLimitError(
                        "Rate limited after maximum retries.", status_code=429
                    )
                time.sleep(BACKOFF_SECONDS * (2 ** (attempt - 1)))
                continue

            if 400 <= response.status_code < 500:
                raise GroqClientError(
                    f"Client error {response.status_code}: {response.text}",
                    status_code=response.status_code,
                )

            if response.status_code >= 500:
                raise GroqServerError(
                    f"Server error {response.status_code}: {response.text}",
                    status_code=response.status_code,
                )

            # Fallback for any unexpected status code.
            raise GroqClientError(
                f"Unexpected status {response.status_code}: {response.text}",
                status_code=response.status_code,
            )

    def ask(
        self,
        question: str,
        csv_path: str,
        temperature: float = 0.0,
        max_tokens: int = 500,
    ) -> GroundedAnswer | dict:
        """High-level grounded QA call.

        Returns a GroundedAnswer on success. If the model's content cannot be
        parsed as valid structured JSON, returns a dict describing the parse
        failure instead of raising, so callers never crash on a bad response.
        """
        rows = load_rows(csv_path)
        relevant_rows = select_relevant_rows(question, rows)
        data_block = rows_to_prompt_block(relevant_rows)
        messages = prompts.build_messages(question, data_block)

        response = self.chat_completion(
            messages, temperature=temperature, max_tokens=max_tokens
        )

        usage = response.get("usage", {})
        tracker.log(
            usage.get("prompt_tokens", 0), usage.get("completion_tokens", 0)
        )

        raw_content = response["choices"][0]["message"]["content"]

        try:
            return parse_model_content(raw_content)
        except ResponseParsingError as exc:
            return {"error": "unparsable_response", "detail": str(exc), "raw": raw_content}
