import json

import pytest

from groundedqa.exceptions import ResponseParsingError
from groundedqa.schema import GroundedAnswer, parse_model_content


def test_parse_valid_json(valid_json_content):
    result = parse_model_content(valid_json_content)
    assert isinstance(result, GroundedAnswer)
    assert result.confidence == "high"
    assert result.source_rows == ["C001"]


def test_parse_not_in_data(not_in_data_content):
    result = parse_model_content(not_in_data_content)
    assert result.answer == "NOT_IN_DATA"


def test_parse_strips_markdown_fences():
    content = "```json\n" + json.dumps(
        {"answer": "x", "source_rows": [], "confidence": "low"}
    ) + "\n```"
    result = parse_model_content(content)
    assert result.answer == "x"


def test_parse_invalid_json_raises():
    with pytest.raises(ResponseParsingError):
        parse_model_content("this is not json at all {")


def test_parse_non_object_json_raises():
    with pytest.raises(ResponseParsingError):
        parse_model_content(json.dumps(["a", "list", "not", "a", "dict"]))


def test_parse_missing_field_raises():
    content = json.dumps({"answer": "x", "confidence": "high"})
    with pytest.raises(ResponseParsingError):
        parse_model_content(content)


def test_parse_wrong_type_answer_raises():
    content = json.dumps({"answer": 123, "source_rows": [], "confidence": "high"})
    with pytest.raises(ResponseParsingError):
        parse_model_content(content)


def test_parse_wrong_type_source_rows_raises():
    content = json.dumps({"answer": "x", "source_rows": "C001", "confidence": "high"})
    with pytest.raises(ResponseParsingError):
        parse_model_content(content)


def test_parse_invalid_confidence_raises():
    content = json.dumps({"answer": "x", "source_rows": [], "confidence": "super-sure"})
    with pytest.raises(ResponseParsingError):
        parse_model_content(content)


def test_parse_none_raises():
    with pytest.raises(ResponseParsingError):
        parse_model_content(None)
