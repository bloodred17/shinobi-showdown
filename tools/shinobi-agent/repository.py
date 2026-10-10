"""Export committed Git blobs without touching the user's worktree or running code."""

import io
from pathlib import Path, PurePosixPath
import subprocess

from deepagents.backends import FilesystemBackend
from deepagents.backends.protocol import DeleteResult, EditResult, WriteResult

MAX_SNAPSHOT_BYTES = 100 * 1024 * 1024
MAX_FILE_BYTES = 1024 * 1024


def git(root: Path, *args: str, data: bytes | None = None) -> bytes:
    result = subprocess.run(
        ["git", "--no-optional-locks", "-c", "core.fsmonitor=false", "-c", "core.hooksPath=/dev/null", "-C", str(root), *args],
        input=data, capture_output=True, timeout=30,
    )
    if result.returncode:
        raise ValueError(f"Git inspection failed: {result.stderr.decode(errors='replace')[:400]}")
    return result.stdout


def safe_path(path: str) -> str:
    # Model-visible /repo prefix is optional in citations, never a host path.
    path = path.removeprefix("/repo/")
    p = PurePosixPath(path)
    if not path or p.is_absolute() or any(x in {"..", ".git"} for x in p.parts) or "\\" in path:
        raise ValueError("Invalid repository-relative path")
    return p.as_posix()


def snapshot(repository: str, revision: str, destination: Path) -> dict:
    source = Path(repository).expanduser().resolve(strict=True)
    root = Path(git(source, "rev-parse", "--show-toplevel").decode().strip())
    commit = git(root, "rev-parse", "--verify", "--end-of-options", revision + "^{commit}").decode().strip()
    rows = git(root, "ls-tree", "-r", "-z", "-l", commit).split(b"\0")
    entries, excluded = [], []
    total = 0
    for row in filter(None, rows):
        header, raw_path = row.split(b"\t", 1)
        mode, kind, oid, size = header.split()
        path = safe_path(raw_path.decode("utf-8", errors="strict"))
        if mode not in {b"100644", b"100755"} or kind != b"blob":
            excluded.append({"path": path, "reason": "symlink or submodule"})
            continue
        length = int(size)
        if length > MAX_FILE_BYTES:
            excluded.append({"path": path, "reason": "larger than 1 MiB"})
            continue
        total += length
        entries.append((path, oid, length))
    if total > MAX_SNAPSHOT_BYTES or len(entries) > 10000:
        raise ValueError("Repository exceeds the Slice 1 snapshot limit (100 MiB / 10000 files)")
    # Batch by object ID: no checkout filters, hooks, export-subst, or shell interpolation.
    content = io.BytesIO(git(root, "cat-file", "--batch", data=b"".join(oid + b"\n" for _, oid, _ in entries)))
    destination.mkdir(parents=True)
    for path, oid, size in entries:
        header = content.readline().split()
        if header != [oid, b"blob", str(size).encode()]:
            raise ValueError("Unexpected Git blob response")
        blob = content.read(size)
        if content.read(1) != b"\n":
            raise ValueError("Incomplete Git blob response")
        try:
            blob.decode("utf-8")
            if b"\0" in blob:
                raise UnicodeError()
        except UnicodeError:
            excluded.append({"path": path, "reason": "binary or non-UTF-8"})
            continue
        target = destination / path
        target.parent.mkdir(parents=True, exist_ok=True)
        target.write_bytes(blob)
        target.chmod(0o444)
    dirty = bool(git(root, "status", "--porcelain", "--untracked-files=normal"))
    return {"repository": str(root), "revision": commit, "dirty_at_creation": dirty, "excluded": excluded}


class ReadOnlyRepository(FilesystemBackend):
    """Deny mutations even if a tool is called directly rather than by the model."""

    def __init__(self, root: Path, reads: list[dict]):
        super().__init__(root_dir=root, virtual_mode=True)
        self.reads = reads

    def read(self, file_path, offset=0, limit=2000):
        result = super().read(file_path, offset, limit)
        if not result.error and result.start_line is not None:
            self.reads.append({"path": file_path.lstrip("/"), "start": result.start_line,
                               "end": result.end_line})
        return result

    def write(self, file_path, content):
        return WriteResult(error="Repository is read-only; this slice only proposes changes.")

    def edit(self, file_path, old_string, new_string, replace_all=False):
        return EditResult(error="Repository is read-only; this slice only proposes changes.")

    def delete(self, file_path):
        return DeleteResult(error="Repository is read-only; this slice only proposes changes.")

    def upload_files(self, files):
        raise PermissionError("Repository uploads are disabled")


def validate_evidence(outcome, root: Path, reads: list[dict]):
    for item in outcome.evidence:
        path = safe_path(item.path)
        target = root / path
        if not target.is_file() or target.is_symlink():
            raise ValueError(f"Citation references an unavailable file: {path}")
        lines = len(target.read_text().splitlines())
        if not 1 <= item.start_line <= item.end_line <= lines:
            raise ValueError(f"Citation has an invalid line range: {path}")
        if not any(r["path"] == path and r["start"] <= item.start_line and r["end"] >= item.end_line for r in reads):
            raise ValueError(f"Citation was not backed by a file read: {path}")
        item.path = path
    if outcome.proposal:
        outcome.proposal.affected_paths = [safe_path(p) + ("/" if p.endswith("/") else "") for p in outcome.proposal.affected_paths]
