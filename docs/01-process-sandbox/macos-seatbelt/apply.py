"""把旁边的 .sb 规则套到当前这个 Python 进程上。"""

import ctypes
from pathlib import Path


def apply(profile_name: str) -> None:
    profile = (Path(__file__).resolve().parent / profile_name).read_text()
    lib = ctypes.CDLL("/usr/lib/libsandbox.dylib")
    sandbox_init = lib.sandbox_init
    sandbox_init.argtypes = [
        ctypes.c_char_p,
        ctypes.c_uint64,
        ctypes.POINTER(ctypes.c_char_p),
    ]
    sandbox_init.restype = ctypes.c_int

    err = ctypes.c_char_p()
    rc = sandbox_init(profile.encode(), 0, ctypes.byref(err))
    if rc != 0:
        msg = err.value.decode() if err.value else str(rc)
        raise RuntimeError(f"sandbox_init failed: {msg}")
