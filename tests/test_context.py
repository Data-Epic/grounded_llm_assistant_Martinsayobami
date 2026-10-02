from groundedqa.context import load_rows, select_relevant_rows, rows_to_prompt_block


def test_load_rows(sample_csv):
    rows = load_rows(sample_csv)
    assert len(rows) == 4
    assert rows[0]["customer_id"] == "C001"


def test_filter_by_country(sample_csv):
    rows = load_rows(sample_csv)
    result = select_relevant_rows("Which customers are in Nigeria?", rows)
    assert len(result) == 2
    assert all(r["country"] == "Nigeria" for r in result)


def test_filter_by_loyalty_threshold_above(sample_csv):
    rows = load_rows(sample_csv)
    result = select_relevant_rows("Who has a loyalty score above 80?", rows)
    ids = {r["customer_id"] for r in result}
    assert ids == {"C001", "C005"}


def test_filter_by_loyalty_threshold_below(sample_csv):
    rows = load_rows(sample_csv)
    result = select_relevant_rows("Who has a loyalty score below 50?", rows)
    ids = {r["customer_id"] for r in result}
    assert ids == {"C002"}


def test_filter_combined_country_and_threshold(sample_csv):
    rows = load_rows(sample_csv)
    result = select_relevant_rows(
        "Which USA customers have a loyalty score above 80?", rows
    )
    ids = {r["customer_id"] for r in result}
    assert ids == {"C005"}


def test_fallback_sample_when_no_filter_matches(sample_csv):
    rows = load_rows(sample_csv)
    result = select_relevant_rows("What is the capital of France?", rows)
    # falls back to a small default sample, not the whole (small) dataset blindly
    assert len(result) <= 5
    assert len(result) > 0


def test_empty_rows_returns_empty():
    assert select_relevant_rows("anything", []) == []


def test_rows_to_prompt_block_empty():
    assert rows_to_prompt_block([]) == "(no matching rows found)"


def test_rows_to_prompt_block_contains_header_and_data(sample_csv):
    rows = load_rows(sample_csv)
    block = rows_to_prompt_block(rows[:1])
    assert "customer_id" in block
    assert "C001" in block
