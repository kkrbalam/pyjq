import pytest
from pyjq.binding import JQ, JQParseError, JQError, Recorder
import os

test_recorder = Recorder(os.path.join(
    os.path.dirname(__file__),
    "..",
    "test.c"
))


def setup_module(module):
    pass


def teardown_module(module):
    test_recorder.write_main_and_exit()


@test_recorder.capture
def test_can_allocate():
    JQ()


@test_recorder.capture
def test_can_compile():
    JQ().compile(".")


@test_recorder.capture
def test_raises_parse_error():
    with pytest.raises(JQParseError) as excinfo:
        JQ().compile("}")
    assert "syntax error" in excinfo.exconly()


@test_recorder.capture
def test_can_pass_data_through():
    jq = JQ()
    jq.compile(".")
    jq.write(1)
    assert list(jq) == [1]
    jq.write(2)
    assert list(jq) == [2]
    assert list(jq) == []


@test_recorder.capture
def test_can_pass_multiple_values_through():
    jq = JQ()
    jq.compile(".")
    jq.write(1)
    jq.write(1)
    assert list(jq) == [1, 1]


@test_recorder.capture
def test_can_select_fields():
    jq = JQ()
    jq.compile(".foo")
    r = range(10) + ["foo", "bar"]
    for v in r:
        jq.write({"foo": v})


@test_recorder.capture
def test_raises_on_bad_json():
    jq = JQ()
    jq.compile(".")
    with pytest.raises(JQError):
        jq.write_string("{11., ]")


@test_recorder.capture
def test_errors_on_incompatible_data_type():
    jq = JQ()
    jq.compile(".foo")
    with pytest.raises(JQError) as excinfo:
        jq.write(1)
    assert "Cannot index number with string" in excinfo.exconly()


@test_recorder.capture
def test_multiple_jq_are_independent():
    jq1 = JQ()
    jq2 = JQ()
    with pytest.raises(JQParseError):
        jq1.compile(".}")
    jq3 = JQ()

    jq2.compile(".")
    jq3.compile(".foo")
    jq2.write("foo")
    jq2.write(1)
    jq3.write({"foo": 10})
    assert list(jq2) == ["foo", 1]
    assert list(jq3) == [10]


def test_can_resume_iteration():
    jq = JQ()
    jq.compile(".[]")
    jq.write([1, 2, 3, 4])
    for i in jq:
        assert i == 1
        break
    jq.write([5, 6])
    assert list(jq) == [2, 3, 4, 5, 6]
