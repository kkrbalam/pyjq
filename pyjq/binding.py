import ctypes
import ctypes.util
import os
import gc
import json
from contextlib import contextmanager
import functools
import threading
from pyjq.rotatingbuffer import RotatingBuffer


class JQError(Exception):
    pass


class JQParseError(JQError):
    pass


recorder = threading.local()
recorder.current = None


class Recorder(object):
    def __init__(self, filename):
        self.f = open(filename, "w")
        self.names = {}
        self.i = 1
        self.indent = 0
        self.functions = []
        self.write("#include <pyjq/compat.c>")

    @contextmanager
    def new_function(self, name):
        self.functions.append(name)
        old_names = self.names
        old_i = self.i
        old_indent = self.indent
        self.i = 0
        self.names = {}
        try:
            self.write("\n")
            self.write("void %s(){" % name)
            self.indent += 2
            yield
        finally:
            self.i = old_i
            self.names = old_names
            self.indent = old_indent
            self.write("}")

    def write(self, text):
        for line in text.splitlines():
            self.f.write(" " * self.indent)
            self.f.write(line)
            self.f.write("\n")
        self.f.flush()

    def new_name(self):
        result = "jqc%d" % self.i
        self.i += 1
        return result

    def translate(self, arg):
        try:
            return self.names[arg]
        except (KeyError, TypeError):
            if isinstance(arg, ctypes.c_char_p):
                arg = '"%s"' % repr(arg.value)[1:-1].replace('"', '\\"')
            return str(arg)

    def record_new(self, new_jqc):
        name = self.new_name()
        self.names[new_jqc] = name
        self.write("jq_compat *%s = jq_compat_new();" % name)

    def record(self, name, args):
        self.write("%s(%s);" % (name, ', '.join(map(self.translate, args))))
        self.f.flush()

    def capture(self, fn):
        @functools.wraps(fn)
        def captured():
            old_recorder = recorder.current
            try:
                recorder.current = self
                with self.new_function(fn.__name__):
                    result = fn()
                    gc.collect()
                    return result
            finally:
                recorder.current = old_recorder
        return captured

    def write_main_and_exit(self):
        functions = list(self.functions)
        self.write("\n")
        self.write("int main(){")
        for function in functions:
            self.write("  %s();" % function)
        self.write("  return 0;")
        self.write("}")
        self.f.close()


class JQ(object):
    lib = ctypes.cdll.LoadLibrary(os.path.join(
        os.path.dirname(__file__),
        "compat.so"
    ))

    lib.jq_compat_new.restype = ctypes.c_size_t
    lib.jq_compat_compile.restype = int
    lib.jq_compat_read_error.restype = ctypes.c_char_p
    lib.jq_compat_read_output.restype = ctypes.c_char_p

    def __init__(self):
        self.compat = None
        self.recorder = recorder.current
        self.compat = self._invoke("jq_compat_new")
        self.pending_objects = RotatingBuffer()
        if self.recorder:
            self.recorder.record_new(self.compat)

    def __del__(self):
        if self.compat:
            self.invoke("del")
            self.compat = None

    def compile(self, program):
        with self.__check_error(JQParseError):
            self.invoke("compile", ctypes.c_char_p(program))

    def write(self, value):
        self.write_string(json.dumps(value))

    def write_string(self, s):
        with self.__check_error():
            self.invoke(
                "write",
                len(s),
                ctypes.c_char_p(s)
            )

    def __iter__(self):
        data = map(json.loads, str(self.invoke("read_output")).splitlines())
        for o in data:
            self.pending_objects.push(o)
        return self.pending_objects

    def invoke(self, name, *args):
        args = ((self.compat,) + args)
        name = "jq_compat_" + name
        if self.recorder:
            self.recorder.record(name, args)
        return self._invoke(name, *args)

    def _invoke(self, name, *args):
        return getattr(self.lib, name)(*args)

    @contextmanager
    def __check_error(self, exc=JQError):
        self.invoke("clear_error")
        yield
        if self.lib.jq_compat_had_error(self.compat):
            current_error = str(self.invoke("read_error"))
            raise exc(str(current_error))
