# groundedqa

A small Python package that answers questions using **only** a supplied dataset
(`data/mock.csv`, customer records), via the Groq chat completions endpoint
(`requests`, not the Groq SDK). If the answer isn't in the data, the model is
instructed to reply `NOT_IN_DATA`.

See [REPORT.md](./REPORT.md) for the prompt design rationale, temperature
comparison, a confidently-wrong case, and token accounting.

## Install

```bash
poetry install
cp .env.example .env
# edit .env and paste your Groq API key (console.groq.com)
```

## Usage

```bash
poetry run ask "Which customers in Nigeria have a loyalty score above 80?"
poetry run ask "What is the capital of France?"          # -> NOT_IN_DATA
poetry run compare "Who has the highest loyalty score in Kenya?"
```

`ask` accepts optional flags: `--csv <path>`, `--temperature <float>`, `--max-tokens <int>`.
`compare` runs the same question at temperature 0 and temperature 1, three times each.

Token usage (prompt/completion/total) is logged per call and a running total is
printed when the program exits.

## How context is managed

Instead of sending the whole CSV on every request, `groundedqa/context.py`
looks for a country name or a loyalty-score comparison (e.g. "above 80",
"below 50") in the question and filters the dataset down to just the matching
rows before they go into the prompt. If neither is found, it falls back to a
small default sample rather than sending everything. See REPORT.md for the
estimated token savings.

## Tests & coverage

```bash
poetry run pytest --cov=groundedqa --cov-report=term-missing
```

Coverage output (31 tests, mocked HTTP — no real calls to Groq are made):

```
Name                          Stmts   Miss  Cover   Missing
-----------------------------------------------------------
groundedqa/__init__.py            1      0   100%
groundedqa/cli.py                41      1    98%   62
groundedqa/client.py             56      1    98%   89
groundedqa/context.py            62      7    89%   75-76, 81-85
groundedqa/exceptions.py          8      0   100%
groundedqa/prompts.py              5      0   100%
groundedqa/schema.py              39      0   100%
groundedqa/token_tracker.py       21      4    81%   20, 23, 34-35
-----------------------------------------------------------
TOTAL                            233     13    94%
31 passed in 0.69s
```

Test cases covered: successful JSON response, non-JSON response (handled
without crashing), a 429 followed by success, a 401, a 5xx, and the
`NOT_IN_DATA` path — with success and failure paths tested for every public
method.

## Project layout

```
groundedqa/
  client.py         # GroqClient: HTTP calls, retries, token logging
  prompts.py        # all prompt templates in one place
  context.py        # relevant-row selection (context management)
  schema.py         # structured-output parsing & validation
  exceptions.py     # custom exception classes
  token_tracker.py  # running token total, printed on exit
  cli.py            # `ask` and `compare` Poetry scripts
data/mock.csv       # sample customer dataset
tests/              # pytest suite, HTTP fully mocked
```

## Security notes

- API key is loaded from `.env` via `python-dotenv` and sent as a bearer token.
- `.env` is git-ignored; `.env.example` is committed instead.
- No API keys are hard-coded, logged, or printed anywhere in the code.
