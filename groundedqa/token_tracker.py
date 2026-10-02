"""Tracks prompt/completion token usage across a run and prints a total on exit."""
from __future__ import annotations

import atexit


class TokenTracker:
    def __init__(self):
        self.prompt_tokens = 0
        self.completion_tokens = 0
        self.calls = 0

    def log(self, prompt_tokens: int, completion_tokens: int) -> None:
        self.prompt_tokens += prompt_tokens
        self.completion_tokens += completion_tokens
        self.calls += 1

    @property
    def total_tokens(self) -> int:
        return self.prompt_tokens + self.completion_tokens

    def summary(self) -> str:
        return (
            f"[groundedqa] Token usage — calls: {self.calls}, "
            f"prompt: {self.prompt_tokens}, completion: {self.completion_tokens}, "
            f"total: {self.total_tokens}"
        )


tracker = TokenTracker()


def _print_summary_on_exit():
    if tracker.calls:
        print(tracker.summary())


atexit.register(_print_summary_on_exit)
