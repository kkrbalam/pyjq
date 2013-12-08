from pyjq.binding import JQ


class Filter(object):
    def __init__(self, text):
        assert isinstance(text, basestring)
        if isinstance(text, unicode):
            text = text.encode('utf8')
        JQ().compile(text)
        self.text = text

    def compose(self, other):
        if isinstance(other, basestring):
            other = Filter(other)
        else:
            assert isinstance(other, Filter)
        return Filter(self.text + " | " + other.text)

    __or__ = compose

    def run(self, stream):
        jq = JQ()
        jq.compile(self.text)
        for item in stream:
            jq.write(item)
            for result in jq:
                yield result

    __call__ = run

jq = Filter
