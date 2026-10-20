"""Trusted bootstrap. Execute a host-configured worker only after enforcement."""
import ctypes
import errno
import hashlib
import json
import os
import resource
import sys
import time

# Preloaded for in-memory workers; imports needing filesystem access later fail.
import socket
import subprocess
import threading

PROFILE = 'seccomp_python_stdio_v1'
ALLOW = ('brk', 'mmap', 'mprotect', 'munmap', 'mremap', 'madvise',
         'rt_sigaction', 'rt_sigprocmask', 'rt_sigreturn', 'sigaltstack',
         'futex', 'getpid', 'gettid', 'clock_gettime', 'clock_nanosleep',
         'nanosleep', 'sched_yield', 'getrandom', 'exit', 'exit_group', 'close')


class Comparison(ctypes.Structure):
    _fields_ = [('arg', ctypes.c_uint), ('op', ctypes.c_int),
                ('a', ctypes.c_uint64), ('b', ctypes.c_uint64)]


def policy_hash(limits):
    policy = {'profile': PROFILE, 'allow': ALLOW,
              'read_fds': [0], 'write_fds': [1, 2], 'limits': limits}
    return hashlib.sha256(json.dumps(policy, sort_keys=True).encode()).hexdigest()


def enforce():
    if sys.platform != 'linux' or os.uname().machine != 'x86_64':
        raise RuntimeError('restricted profile supports Linux x86-64 only')
    lib = ctypes.CDLL('libseccomp.so.2', use_errno=True)
    lib.seccomp_init.argtypes = [ctypes.c_uint32]
    lib.seccomp_init.restype = ctypes.c_void_p
    lib.seccomp_syscall_resolve_name.argtypes = [ctypes.c_char_p]
    lib.seccomp_syscall_resolve_name.restype = ctypes.c_int
    lib.seccomp_rule_add.argtypes = [ctypes.c_void_p, ctypes.c_uint32,
                                    ctypes.c_int, ctypes.c_uint]
    lib.seccomp_load.argtypes = [ctypes.c_void_p]
    lib.seccomp_release.argtypes = [ctypes.c_void_p]
    libc = ctypes.CDLL(None, use_errno=True)
    if libc.prctl(38, 1, 0, 0, 0) != 0:  # PR_SET_NO_NEW_PRIVS
        raise RuntimeError('no_new_privs unavailable')
    ctx = lib.seccomp_init(0x00050000 | errno.EPERM)
    if not ctx:
        raise RuntimeError('seccomp_init failed')
    try:
        for name in ALLOW:
            number = lib.seccomp_syscall_resolve_name(name.encode())
            if number < 0 or lib.seccomp_rule_add(ctx, 0x7fff0000, number, 0) != 0:
                raise RuntimeError('cannot allow syscall ' + name)
        for name, fds in [('read', [0]), ('readv', [0]),
                          ('write', [1, 2]), ('writev', [1, 2])]:
            number = lib.seccomp_syscall_resolve_name(name.encode())
            for fd in fds:
                if number < 0 or lib.seccomp_rule_add(
                        ctx, 0x7fff0000, number, 1, Comparison(0, 4, fd, 0)) != 0:
                    raise RuntimeError('cannot restrict stdio')
        if lib.seccomp_load(ctx) != 0:
            raise RuntimeError('seccomp_load failed')
    finally:
        lib.seccomp_release(ctx)


def main():
    raw = sys.stdin.buffer.readline(8_000_002)
    if len(raw) > 8_000_001 or not raw.endswith(b'\n'):
        raise RuntimeError('startup packet too large')
    packet = json.loads(raw)
    code = packet.pop('worker_source')
    limits = packet.pop('limits')
    worker_hash = hashlib.sha256(code.encode()).hexdigest()
    bootstrap_hash = hashlib.sha256(open(__file__, 'rb').read()).hexdigest()
    prompt_hash = hashlib.sha256(packet['prompt'].encode()).hexdigest()
    for kind, value in [(resource.RLIMIT_AS, limits['memory_bytes']),
                        (resource.RLIMIT_CPU, limits['cpu_seconds']),
                        (resource.RLIMIT_CORE, 0), (resource.RLIMIT_FSIZE, 0),
                        (resource.RLIMIT_NOFILE, 16)]:
        resource.setrlimit(kind, (value, value))
    compiled = compile(code, '<host-configured-worker>', 'exec')
    os.closerange(3, 1_048_576)
    # Filter installation is the last operation before readiness and worker exec.
    enforce()
    ready = {'profile': PROFILE, 'pid': os.getpid(), 'prompt_sha256': prompt_hash,
             'worker_sha256': worker_hash, 'bootstrap_sha256': bootstrap_hash,
             'policy_sha256': policy_hash(limits), 'limits': limits}
    def write_all(raw):
        view = memoryview(raw)
        while view:
            view = view[os.write(1, view):]
    write_all(json.dumps({'ready': ready}).encode() + b'\n')
    # Do not enter payload code until the parent has verified this exact frame.
    token = hashlib.sha256(json.dumps(ready, sort_keys=True).encode()).hexdigest()
    ack = sys.stdin.buffer.readline(1025)
    if len(ack) > 1024 or json.loads(ack) != {'execute': token}:
        raise RuntimeError('missing or invalid host execution acknowledgment')
    namespace = {'__name__': 'atc_restricted_payload', 'json': json,
                 'hashlib': hashlib, 'time': time}
    exec(compiled, namespace)
    response = namespace['run'](packet)
    write_all(json.dumps(response, ensure_ascii=False, allow_nan=False).encode())


if __name__ == '__main__':
    main()
