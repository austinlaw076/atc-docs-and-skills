"""Benign canary probes for the restricted process, never a production worker."""


def run(packet):
    import ctypes
    import os
    import socket
    import subprocess
    import threading
    e = packet['envelope']
    path = e['path']
    checks = {}
    def fork_probe():
        pid = os.fork()
        if pid == 0:
            os._exit(99)
        os.waitpid(pid, 0)
    actions = {
        'file_read': lambda: open(path), 'file_write': lambda: open(path, 'w'),
        'file_append': lambda: open(path, 'a'), 'symlink_read': lambda: open(e['link']),
        'traversal_read': lambda: open(e['traversal']), 'unlink': lambda: os.unlink(path),
        'mkdir': lambda: os.mkdir(path + '.dir'),
        'symlink_create': lambda: os.symlink(path, path + '.new'),
        'tcp_socket': lambda: socket.socket(),
        'udp_socket': lambda: socket.socket(type=socket.SOCK_DGRAM),
        'unix_socket': lambda: socket.socket(socket.AF_UNIX), 'fork': fork_probe,
        'external_tool': lambda: subprocess.run(['/bin/true'], check=True),
        'thread': lambda: threading.Thread(target=lambda: None).start()}
    for name, action in actions.items():
        try:
            action()
            checks[name] = {'denied': False}
        except PermissionError as exc:
            checks[name] = {'denied': True, 'errno': exc.errno}
        except RuntimeError as exc:
            checks[name] = {'denied': name == 'thread', 'error': str(exc)}
    libc = ctypes.CDLL(None, use_errno=True)
    how = ctypes.create_string_buffer(24)
    raw = {'native_open': (2, path.encode(), 0), 'native_openat': (257, -100, path.encode(), 0),
        'native_openat2': (437, -100, path.encode(), ctypes.byref(how), 24),
        'ptrace': (101, 16, e['parent'], 0, 0),
        'parent_memory': (310, e['parent'], 0, 0, 0, 0, 0),
        'parent_signal_probe': (62, e['parent'], 0), 'filter_change': (317, 1, 0, 0),
        'privilege_change': (157, 38, 0, 0, 0, 0), 'native_execve': (59, b'/bin/true', 0, 0)}
    for name, args in raw.items():
        ctypes.set_errno(0)
        value = libc.syscall(*args)
        error = ctypes.get_errno()
        checks[name] = {'denied': value == -1 and error == 1, 'return': value, 'errno': error}
    return {'checks': checks, 'provenance': 'real child-process canary probes; no model involved'}
