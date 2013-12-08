import ctypes
import ctypes.util
import os
import json


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
        buff = ctypes.create_string_buffer(program)
        compiled = self.lib.jq_compat_compile(self.compat, buff)
        if not compiled:
            self.__check_error(JQParseError)

    def write(self, value):
        json_data = json.dumps(value)
        self.lib.jq_compat_write(
            self.compat,
            len(json_data),
            ctypes.c_char_p(json_data)
        )

    def __iter__(self):
        data = str(self.lib.jq_compat_read_output(self.compat))
        for line in data.splitlines():
            yield json.loads(line)

    def __check_error(self, exc=JQError):
        current_error = str(self.lib.jq_compat_read_error(self.compat))
        if current_error:
            raise exc(str(current_error))
