import ctypes
import ctypes.util
import os
import json
from contextlib import contextmanager


class JQCompat(ctypes.Structure):
    pass


class JQError(Exception):
    pass


class JQParseError(JQError):
    pass


class JQ(object):
    lib = ctypes.cdll.LoadLibrary(os.path.join(
        os.path.dirname(__file__),
        "compat.so"
    ))

    lib.jq_compat_new.restype = ctypes.POINTER(JQCompat)
    lib.jq_compat_compile.restype = int
    lib.jq_compat_read_error.restype = ctypes.c_char_p
    lib.jq_compat_read_output.restype = ctypes.c_char_p

    def __init__(self):
        self.compat = self._invoke("new")

    def __del__(self):
        self.invoke("del")

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
        data = str(self.invoke("read_output"))
        for line in data.splitlines():
            yield json.loads(line)

    def invoke(self, name, *args):
        return self._invoke(name, *((self.compat,) + args))

    def _invoke(self, name, *args):
        name = "jq_compat_" + name
        return getattr(self.lib, name)(*args)

    @contextmanager
    def __check_error(self, exc=JQError):
        self.invoke("clear_error")
        yield
        if self.lib.jq_compat_had_error(self.compat):
            current_error = str(self.invoke("read_error"))
            raise exc(str(current_error))
