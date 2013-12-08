from pyjq import jq


def test_supports_no_op():
    xs = range(10)
    assert list(jq(".")(xs)) == xs


def test_selects_fields():
    assert list(jq(".foo")({"foo": i} for i in range(100))) == range(100)


def test_compose_filters():
    composed = jq(".foo") | ".[]"
    assert list(composed([{"foo": [1, 2, 3]}])) == [1, 2, 3]


def test_explode_list():
    xs = range(10)
    assert list(jq(".[]")([xs])) == xs
