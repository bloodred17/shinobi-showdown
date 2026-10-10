"""OS isolation for every repository operation; no unsandboxed fallback."""
import json
import os
from pathlib import Path
import selectors
import shutil
import signal
import subprocess
import time

MAX_OUTPUT = 128 * 1024


class Sandbox:
    def __init__(self, workspace: Path, guard=lambda: None):
        self.workspace = workspace.resolve(strict=True)
        self.guard = guard
        if not shutil.which("bwrap") or not shutil.which("prlimit"):
            raise RuntimeError("Bubblewrap and prlimit are required; execution remains blocked")

    def command(self, argv, writable=False, cwd="."):
        command = ["/usr/bin/prlimit", "--as=8589934592", "--cpu=120", "--fsize=16777216", "--nofile=128", "--",
                   shutil.which("bwrap"), "--unshare-all", "--unshare-user", "--disable-userns", "--die-with-parent", "--new-session",
                   "--cap-drop", "ALL", "--clearenv"]
        for path in ("/usr", "/bin", "/lib", "/lib64"):
            if Path(path).exists():
                command += ["--ro-bind", path, path]
        if Path("/etc/ld.so.cache").exists():
            command += ["--ro-bind", "/etc/ld.so.cache", "/etc/ld.so.cache"]
        command += ["--proc", "/proc", "--dev", "/dev", "--size", "67108864", "--tmpfs", "/tmp",
                    "--dir", "/tmp/home", "--setenv", "HOME", "/tmp/home", "--setenv", "PATH", "/usr/bin:/bin",
                    "--setenv", "LANG", "C.UTF-8", "--setenv", "PYTHONDONTWRITEBYTECODE", "1",
                    "--setenv", "PYTHONPYCACHEPREFIX", "/tmp/pycache", "--setenv", "npm_config_cache", "/tmp/npm",
                    "--setenv", "NX_DAEMON", "false", "--setenv", "NX_ISOLATE_PLUGINS", "false",
                    "--setenv", "NX_WORKSPACE_DATA_DIRECTORY", "/tmp/nx-data", "--setenv", "NX_CACHE_DIRECTORY", "/tmp/nx-cache",
                    "--setenv", "GIT_CONFIG_NOSYSTEM", "1", "--setenv", "GIT_CONFIG_GLOBAL", "/dev/null",
                    "--bind" if writable else "--ro-bind", str(self.workspace), "/workspace",
                    "--ro-bind", str(Path(__file__).with_name("sandbox_fileop.py")), "/fileop.py",
                    "--chdir", "/workspace" + ("" if cwd == "." else "/" + cwd), "--", *argv]
        return command

    def execute(self, argv, *, writable=False, cwd=".", timeout=60, data=None):
        self.guard()
        started = time.monotonic()
        child = subprocess.Popen(self.command(argv, writable, cwd), stdin=subprocess.PIPE,
                                 stdout=subprocess.PIPE, stderr=subprocess.PIPE,
                                 env={"PATH": "/usr/bin:/bin"}, start_new_session=True)
        output = {"stdout": bytearray(), "stderr": bytearray()}
        selector = selectors.DefaultSelector()
        try:
            child.stdin.write(data or b"")
            child.stdin.close()
            for pipe, name in [(child.stdout, "stdout"), (child.stderr, "stderr")]:
                selector.register(pipe, selectors.EVENT_READ, name)
            while selector.get_map():
                self.guard()
                if time.monotonic() - started > timeout:
                    raise TimeoutError("Sandbox operation exceeded its approved timeout")
                for key, _ in selector.select(0.1):
                    chunk = os.read(key.fileobj.fileno(), 16384)
                    if not chunk:
                        selector.unregister(key.fileobj)
                    else:
                        output[key.data].extend(chunk)
                        if sum(len(v) for v in output.values()) > MAX_OUTPUT:
                            raise RuntimeError("Sandbox output exceeds 128 KiB")
            code = child.wait(timeout=max(0.1, timeout - (time.monotonic() - started)))
            self.guard()
            return {"argv": argv, "cwd": cwd, "exit_code": code,
                    **{k: bytes(v).decode(errors="replace") for k, v in output.items()},
                    "seconds": round(time.monotonic() - started, 3)}
        finally:
            selector.close()
            if child.poll() is None:
                os.killpg(child.pid, signal.SIGKILL)
                child.wait(timeout=5)
            child.stdout.close()
            child.stderr.close()

    def preflight(self):
        result = self.execute(["/usr/bin/true"], timeout=10)
        if result["exit_code"]:
            raise RuntimeError("Sandbox unavailable; no repository code ran: " + result["stderr"][:500])

    def file(self, operation, path=".", scopes=(), **args):
        payload = json.dumps({"operation": operation, "path": path, "scopes": list(scopes), **args}).encode()
        if len(payload) > 2 * 1024 * 1024:
            raise ValueError("File operation payload too large")
        result = self.execute(["/usr/bin/python3.12", "-I", "/fileop.py"],
                              writable=operation in {"write", "edit", "delete"}, data=payload)
        if result["exit_code"]:
            raise ValueError("Sandbox file operation failed: " + result["stdout"][:1000] + result["stderr"][:500])
        return json.loads(result["stdout"])["result"]
