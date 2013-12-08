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
        self.compat = self.lib.jq_compat_new()

    def __del__(self):
        self.lib.jq_compat_del(self.compat)

    def compile(self, program):
        with self.__check_error(JQParseError):
            self.lib.jq_compat_compile(self.compat, ctypes.c_char_p(program))

    def write(self, value):
        self.write_string(json.dumps(value))

    def write_string(self, s):
        with self.__check_error():
            self.lib.jq_compat_write(
                self.compat,
                len(s),
                ctypes.c_char_p(s)
            )

    def __iter__(self):
        data = str(self.lib.jq_compat_read_output(self.compat))
        for line in data.splitlines():
            yield json.loads(line)

    @contextmanager
    def __check_error(self, exc=JQError):
        self.lib.jq_compat_clear_error(self.compat)
        yield
        if self.lib.jq_compat_had_error(self.compat):
            current_error = str(self.lib.jq_compat_read_error(self.compat))
            raise exc(str(current_error))
