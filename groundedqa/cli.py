"""Poetry console-script entry points: `ask "<question>"` and `compare "<question>"`."""
from __future__ import annotations

import argparse
import sys
from pathlib import Path

from .client import GroqClient
from .schema import GroundedAnswer

DEFAULT_CSV = str(Path(__file__).resolve().parent.parent / "data" / "mock.csv")


def _print_result(result) -> None:
    if isinstance(result, GroundedAnswer):
        print(f"Answer: {result.answer}")
        print(f"Source rows: {result.source_rows}")
        print(f"Confidence: {result.confidence}")
    else:
        print(f"[parse error] {result.get('detail')}")
        print(f"Raw content: {result.get('raw')!r}")


def ask_main(argv=None) -> int:
    parser = argparse.ArgumentParser(prog="ask", description="Ask a grounded question.")
    parser.add_argument("question", help="The question to ask.")
    parser.add_argument("--csv", default=DEFAULT_CSV, help="Path to the dataset CSV.")
    parser.add_argument("--temperature", type=float, default=0.0)
    parser.add_argument("--max-tokens", type=int, default=500)
    args = parser.parse_args(argv)

    client = GroqClient()
    result = client.ask(
        args.question, args.csv, temperature=args.temperature, max_tokens=args.max_tokens
    )
    _print_result(result)
    return 0


def compare_main(argv=None) -> int:
    parser = argparse.ArgumentParser(
        prog="compare", description="Run a question at temperature 0 and 1, 3x each."
    )
    parser.add_argument("question", help="The question to ask.")
    parser.add_argument("--csv", default=DEFAULT_CSV, help="Path to the dataset CSV.")
    parser.add_argument("--max-tokens", type=int, default=500)
    args = parser.parse_args(argv)

    client = GroqClient()
    for temperature in (0.0, 1.0):
        print(f"\n=== temperature={temperature} ===")
        for i in range(3):
            print(f"-- run {i + 1} --")
            result = client.ask(
                args.question, args.csv, temperature=temperature, max_tokens=args.max_tokens
            )
            _print_result(result)
    return 0


if __name__ == "__main__":
    sys.exit(ask_main())
