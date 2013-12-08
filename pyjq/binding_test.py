import pytest
from pyjq.binding import JQ, JQParseError, JQError


def test_can_allocate():
    JQ()


def test_can_compile():
    JQ().compile(".")


def test_raises_parse_error():
    with pytest.raises(JQParseError) as excinfo:
        JQ().compile("}")
    assert "syntax error" in excinfo.exconly()


def test_can_pass_data_through():
    jq = JQ()
    jq.compile(".")
    jq.write(1)
    assert list(jq) == [1]
    jq.write(2)
    assert list(jq) == [2]
    assert list(jq) == []


def test_can_pass_multiple_values_through():
    jq = JQ()
    jq.compile(".")
    jq.write(1)
    jq.write(1)
    assert list(jq) == [1, 1]


def test_can_select_fields():
    jq = JQ()
    jq.compile(".foo")
    r = range(10) + ["foo", "bar"]
    for v in r:
        jq.write({"foo": v})


def test_raises_on_bad_json():
    jq = JQ()
    jq.compile(".")
    with pytest.raises(JQError):
        jq.write_string("{11., ]")
