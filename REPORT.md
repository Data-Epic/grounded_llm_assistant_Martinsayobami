# REPORT

> Sections marked **[FILL IN AFTER YOUR RUN]** need your real Groq API key and a
> live run — I don't have network access to `api.groq.com` or your key, so I
> built and tested the full pipeline (mocked HTTP, 31 passing tests, 94%
> coverage) but the actual model outputs below are placeholders for you to
> replace with `poetry run ask ...` / `poetry run compare ...` output before
> submitting. Everything else in this report is real.

## 1. Prompt templates and why they're structured this way

All templates live in `groundedqa/prompts.py`, one place, so they're easy to
review and change without hunting through the client code.

- **System message** carries the model's role ("data assistant"), the hard
  constraint ("ONLY the labelled data... never outside knowledge"), the
  refusal instruction (`NOT_IN_DATA`), and the output-format contract (JSON
  with `answer` / `source_rows` / `confidence`). Putting constraints in the
  system message rather than the user message makes them harder for the
  model to "forget" partway through a longer conversation, and keeps the
  per-question user message short and focused.
- **User message** is deliberately ordered *instructions → labelled data →
  question*, per the assignment spec. Instructions first orient the model
  before it sees the data; the question last means it's the most recent thing
  the model reads before generating, which in practice makes it less likely
  to answer a *different* question than the one asked.
- Keeping strict JSON-only output (no markdown fences) simplifies parsing,
  though `schema.py` still defensively strips fences if the model adds them
  anyway.

## 2. Temperature comparison

Question used: `"[FILL IN — the question you ran through `compare`]"`

Command: `poetry run compare "<your question>"`

| Run | temperature=0 | temperature=1 |
|-----|---------------|----------------|
| 1   | *[FILL IN]*   | *[FILL IN]*    |
| 2   | *[FILL IN]*   | *[FILL IN]*    |
| 3   | *[FILL IN]*   | *[FILL IN]*    |

**Observations:** *[FILL IN — typically: temperature 0 gives near-identical
wording across all 3 runs since sampling is close to deterministic; temperature
1 gives more varied phrasing and occasionally a different `confidence` value
or a slightly different `source_rows` selection, even though the underlying
data and grounding constraint stay the same.]*

## 3. A case where the model was confidently wrong

*[FILL IN — run a handful of questions and find one where the model answered
with `"confidence": "high"` but got a fact wrong (e.g. transposed two
customers' scores, or averaged the wrong subset). Paste the question, the raw
JSON response, and the correct answer from `data/mock.csv`.]*

**How I caught it:** *[FILL IN — e.g. "by manually checking `source_rows`
against the CSV" — this is exactly why the schema requires `source_rows`: it
lets you audit which rows the model claims it used.]*

## 4. Context management: token savings

`groundedqa/context.py` filters `data/mock.csv` (30 rows) down to only the
rows matching a country name and/or a loyalty-score comparison found in the
question, instead of sending all 30 rows every time. Using a ~4-characters-per-
token estimate on the actual rendered data block:

| Question | Rows sent | Est. tokens sent | Est. tokens if full CSV sent | Est. savings |
|---|---|---|---|---|
| "Which customers in Nigeria have a loyalty score above 80?" | 3 / 30 | ~56 | ~395 | ~86% |
| "Who has a loyalty score below 50 in Kenya?" | 1 / 30 | ~28 | ~395 | ~93% |
| "What is the average spend of USA customers?" | 4 / 30 | ~64 | ~395 | ~84% |

So filtering typically cut the data portion of the prompt by roughly **85–93%**
on this dataset. Savings will be smaller on questions that don't mention a
country or a numeric threshold, since those fall back to a small 5-row default
sample rather than the full CSV (still a large saving, just less dramatic).

## 5. Token totals

*[FILL IN — after your real run, paste the final line printed on exit, e.g.:]*
```
[groundedqa] Token usage — calls: N, prompt: X, completion: Y, total: Z
```

## 6. What I'd change under a fixed cost budget

- Cache identical questions (same question + same filtered row set) instead
  of re-calling the API every time — a simple keyed dict or SQLite cache would
  avoid paying for repeat demo questions.
- Tighten the loyalty-score/country matcher further (e.g. handle "top N"
  questions) so more questions hit the cheap filtered path instead of the
  default fallback sample.
- Lower `max_tokens` further for short factual answers — the current 500 is
  generous headroom for the JSON wrapper, but most real answers here are one
  sentence.
- Stick with `llama-3.1-8b-instant` (already the smallest/cheapest tier used)
  rather than moving to a larger model, since grounded lookups on a small CSV
  don't need more reasoning capacity.
- Batch the three-repeats-per-temperature `compare` runs only when actively
  debugging temperature behavior, not on every demo run.
