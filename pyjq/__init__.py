from pyjq.binding import JQ


class Filter(object):
    def __init__(self, text):
        assert isinstance(text, basestring)
        if isinstance(text, unicode):
            text = text.encode('utf8')

        self.jq = JQ()
        self.text = text
        self.jq.compile(self.text)

    def compose(self, other):
        if isinstance(other, basestring):
            other = Filter(other)
        else:
            assert isinstance(other, Filter)
        return Filter(self.text + " | " + other.text)

    __or__ = compose

    def run(self, stream):
        for item in stream:
            self.jq.write(item)
            for result in self.jq:
                yield result

    __call__ = run

jq = Filter
