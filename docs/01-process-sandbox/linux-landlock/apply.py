"""把旁边的 .rules 套到当前这个 Python 进程上（Linux Landlock）。"""

import ctypes
import ctypes.util
import os
from pathlib import Path

ROOT = Path(__file__).resolve().parent

SYS_LANDLOCK_CREATE_RULESET = 444
SYS_LANDLOCK_ADD_RULE = 445
SYS_LANDLOCK_RESTRICT_SELF = 446
PR_SET_NO_NEW_PRIVS = 38
LANDLOCK_RULE_PATH_BENEATH = 1

FS_ACCESS = {
    "execute": 1 << 0,
    "write_file": 1 << 1,
    "read_file": 1 << 2,
    "read_dir": 1 << 3,
}

NET_ACCESS = {
    "bind_tcp": 1 << 0,
    "connect_tcp": 1 << 1,
}


class RulesetAttr(ctypes.Structure):
    _fields_ = [
        ("handled_access_fs", ctypes.c_uint64),
        ("handled_access_net", ctypes.c_uint64),
    ]


class PathBeneath(ctypes.Structure):
    _fields_ = [
        ("allowed_access", ctypes.c_uint64),
        ("parent_fd", ctypes.c_int32),
    ]


def _libc():
    lib = ctypes.CDLL(ctypes.util.find_library("c"), use_errno=True)
    lib.syscall.restype = ctypes.c_long
    return lib


def _parse(path: Path) -> tuple[int, int, list[Path]]:
    handled_fs = 0
    handled_net = 0
    allow_files: list[Path] = []
    for raw in path.read_text().splitlines():
        line = raw.split("#", 1)[0].strip()
        if not line:
            continue
        parts = line.split()
        key, rest = parts[0], parts[1:]
        if key == "handled_fs":
            for name in rest:
                handled_fs |= FS_ACCESS[name]
        elif key == "handled_net":
            for name in rest:
                handled_net |= NET_ACCESS[name]
        elif key == "allow_file":
            allow_files.append(ROOT / rest[0])
        else:
            raise ValueError(f"unknown rule: {raw}")
    return handled_fs, handled_net, allow_files


def apply(profile_name: str) -> None:
    handled_fs, handled_net, allow_files = _parse(ROOT / profile_name)
    libc = _libc()

    attr = RulesetAttr(handled_fs, handled_net)
    ruleset_fd = libc.syscall(
        ctypes.c_long(SYS_LANDLOCK_CREATE_RULESET),
        ctypes.byref(attr),
        ctypes.c_size_t(ctypes.sizeof(attr)),
        ctypes.c_uint32(0),
    )
    if ruleset_fd < 0:
        raise OSError(ctypes.get_errno(), "landlock_create_ruleset")

    try:
        for file_path in allow_files:
            parent_fd = os.open(file_path, os.O_RDONLY)
            try:
                rule = PathBeneath(handled_fs, parent_fd)
                rc = libc.syscall(
                    ctypes.c_long(SYS_LANDLOCK_ADD_RULE),
                    ctypes.c_int(ruleset_fd),
                    ctypes.c_uint(LANDLOCK_RULE_PATH_BENEATH),
                    ctypes.byref(rule),
                    ctypes.c_uint32(0),
                )
                if rc < 0:
                    raise OSError(ctypes.get_errno(), f"landlock_add_rule {file_path}")
            finally:
                os.close(parent_fd)

        if libc.prctl(PR_SET_NO_NEW_PRIVS, 1, 0, 0, 0) < 0:
            raise OSError(ctypes.get_errno(), "prctl(NO_NEW_PRIVS)")

        rc = libc.syscall(
            ctypes.c_long(SYS_LANDLOCK_RESTRICT_SELF),
            ctypes.c_int(ruleset_fd),
            ctypes.c_uint32(0),
        )
        if rc < 0:
            raise OSError(ctypes.get_errno(), "landlock_restrict_self")
    finally:
        os.close(ruleset_fd)
