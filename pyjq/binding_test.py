import pytest
from pyjq.binding import JQ, JQParseError


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
    assert next(jq) == 1
    jq.write(2)
    assert next(jq) == 2
    with pytest.raises(StopIteration):
        next(jq)