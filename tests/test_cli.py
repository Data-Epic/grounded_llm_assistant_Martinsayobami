from unittest.mock import patch

from groundedqa import cli
from groundedqa.schema import GroundedAnswer


def test_ask_main_success(sample_csv, capsys):
    fake_result = GroundedAnswer(answer="Nigeria has 2 customers.",
                                  source_rows=["C001", "C002"], confidence="high")
    with patch("groundedqa.cli.GroqClient") as MockClient:
        MockClient.return_value.ask.return_value = fake_result
        rc = cli.ask_main(["How many customers in Nigeria?", "--csv", sample_csv])
    captured = capsys.readouterr()
    assert rc == 0
    assert "Nigeria has 2 customers." in captured.out


def test_ask_main_parse_error(sample_csv, capsys):
    error_result = {"error": "unparsable_response", "detail": "bad json", "raw": "oops"}
    with patch("groundedqa.cli.GroqClient") as MockClient:
        MockClient.return_value.ask.return_value = error_result
        rc = cli.ask_main(["Who?", "--csv", sample_csv])
    captured = capsys.readouterr()
    assert rc == 0
    assert "parse error" in captured.out


def test_compare_main_runs_six_times(sample_csv, capsys):
    fake_result = GroundedAnswer(answer="ok", source_rows=[], confidence="medium")
    with patch("groundedqa.cli.GroqClient") as MockClient:
        MockClient.return_value.ask.return_value = fake_result
        rc = cli.compare_main(["Who has the highest score?", "--csv", sample_csv])
    assert rc == 0
    assert MockClient.return_value.ask.call_count == 6
    captured = capsys.readouterr()
    assert "temperature=0.0" in captured.out
    assert "temperature=1.0" in captured.out
