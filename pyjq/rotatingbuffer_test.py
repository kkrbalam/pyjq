from pyjq.rotatingbuffer import RotatingBuffer


def test_buffer_drains():
    buffer = RotatingBuffer()
    buffer.push(1)
    buffer.push(2)
    buffer.push(3)
    assert list(buffer) == [1, 2, 3]
    assert list(buffer) == []


def test_can_add_midway_through():
    buffer = RotatingBuffer()
    buffer.push(1)
    buffer.push(2)
    assert next(buffer) == 1
    buffer.push(3)
    assert list(buffer) == [2, 3]
