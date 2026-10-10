"""Trusted stdlib-only file operations, executed inside Bubblewrap with -I."""
import json
import os
from pathlib import Path, PurePosixPath
import sys
import tempfile

ROOT = Path("/workspace")


def target(value):
    p = PurePosixPath(value)
    if not value or p.is_absolute() or any(part in {"..", ".git"} for part in p.parts) or "\\" in value:
        raise ValueError("Invalid repository path")
    path = ROOT / p
    if any(parent.is_symlink() for parent in [path, *path.parents]) or not path.resolve().is_relative_to(ROOT):
        raise ValueError("Symlinks and path escapes are forbidden")
    return path


def main():
    request = json.load(sys.stdin)
    operation = request["operation"]
    path = target(request.get("path", "."))
    if operation == "list":
        files = [str(p.relative_to(ROOT)) for p in sorted(path.rglob("*"))
                 if ".git" not in p.relative_to(ROOT).parts and p.is_file() and not p.is_symlink()]
        return files[:10000]
    if operation == "read":
        if path.stat().st_size > 1024 * 1024:
            raise ValueError("File exceeds 1 MiB tool limit")
        lines = path.read_text().splitlines()
        offset = max(0, int(request.get("offset", 0)))
        limit = min(2000, max(1, int(request.get("limit", 2000))))
        return "\n".join(f"{i + 1}: {line}" for i, line in enumerate(lines[offset:offset + limit], offset))
    if operation in {"write", "edit", "delete"}:
        scopes = request["scopes"]
        relative = str(path.relative_to(ROOT))
        if not any(relative == s.rstrip("/") or (s.endswith("/") and relative.startswith(s)) for s in scopes):
            raise ValueError("Path exceeds worker ownership")
        if operation == "delete":
            path.unlink()
        else:
            text = request["content"] if operation == "write" else path.read_text()
            if operation == "edit":
                old = request["old"]
                if not old or text.count(old) != 1:
                    raise ValueError("Edit must match exactly one occurrence")
                text = text.replace(old, request["new"], 1)
            if len(text.encode()) > 1024 * 1024:
                raise ValueError("Content exceeds 1 MiB")
            path.parent.mkdir(parents=True, exist_ok=True)
            temporary = None
            try:
                with tempfile.NamedTemporaryFile(mode="w", encoding="utf-8", dir=path.parent, prefix=".shinobi-write-", delete=False) as file:
                    temporary = Path(file.name)
                    file.write(text)
                    file.flush()
                    os.fsync(file.fileno())
                temporary.chmod(path.stat().st_mode & 0o777 if path.exists() else 0o644)
                os.replace(temporary, path)
            finally:
                if temporary and temporary.exists():
                    temporary.unlink()
        return "ok"
    raise ValueError("Unknown file operation")


if __name__ == "__main__":
    try:
        print(json.dumps({"result": main()}))
    except Exception as exc:
        print(json.dumps({"error": str(exc)}))
        raise SystemExit(1)
