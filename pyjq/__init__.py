import subprocess
import os
import json
import sys
from select import select
import inspect


class ParseError(Exception):
    pass


def validate_jq(filter_string):
    jq = subprocess.Popen(
        ["jq", filter_string],
        stdin=subprocess.PIPE,
        stdout=open(os.devnull),
        stderr=subprocess.PIPE
    )
    jq.stdin.close()
    if jq.wait():
        raise ParseError(jq.stderr.read())


class Filter(object):
    def __init__(self, text):
        assert isinstance(text, basestring)
        if isinstance(text, unicode):
            text = text.encode('utf8')
        self.text = text
        validate_jq(text)

    def compose(self, other):
        if isinstance(other, basestring):
            other = Filter(other)
        else:
            assert isinstance(other, Filter)
        return Filter(self.text + " | " + other.text)

    __or__ = compose

    def run(self, stream):
        jq = subprocess.Popen(
            ["jq", self.text, "-c"],
            stdin=subprocess.PIPE,
            stdout=subprocess.PIPE,
            stderr=sys.stderr,
        )

        try:
            for item in stream:
                json.dump(item, jq.stdin)
                jq.stdin.write("\n")
                jq.stdin.flush()
                while select([jq.stdout], [], [], 0)[0]:
                    print "selecting"
                    yield json.loads(jq.stdout.readline())
            jq.stdin.close()
            for line in jq.stdout:
                yield json.loads(line)
        finally:
            jq.stdin.close()
            jq.terminate()

    __call__ = run

jq = Filter
