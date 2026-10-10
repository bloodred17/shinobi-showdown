"""Independent local Git copies, content identity, and serialized integration."""
import hashlib
import io
import json
import os
from pathlib import Path
import shutil
import stat
import subprocess

from execution_contracts import contains
from repository import MAX_SNAPSHOT_BYTES, git, safe_path


def local_git(root, *args, data=None):
    result = subprocess.run(["/usr/bin/git", "-c", "core.hooksPath=/dev/null", "-c", "core.fsmonitor=false",
                             "-c", "user.name=Shinobi", "-c", "user.email=shinobi@localhost.invalid",
                             "-C", str(root), *args], input=data, capture_output=True, timeout=30,
                            env={"PATH": "/usr/bin:/bin", "HOME": "/nonexistent", "GIT_CONFIG_NOSYSTEM": "1",
                                 "GIT_CONFIG_GLOBAL": "/dev/null", "GIT_TERMINAL_PROMPT": "0"})
    if result.returncode:
        raise ValueError("Local Git operation failed: " + result.stderr.decode(errors="replace")[:1000])
    return result.stdout


def export(source, revision, target):
    entries = []
    total = 0
    for row in filter(None, git(Path(source), "ls-tree", "-r", "-z", "-l", revision).split(b"\0")):
        header, raw_path = row.split(b"\t", 1)
        mode, kind, oid, size = header.split()
        path = safe_path(raw_path.decode())
        if mode not in {b"100644", b"100755"} or kind != b"blob":
            raise ValueError("Execution does not support symlinks or submodules: " + path)
        length = int(size)
        total += length
        entries.append((path, oid, length, mode))
    if total > MAX_SNAPSHOT_BYTES or len(entries) > 10000:
        raise ValueError("Execution snapshot exceeds 100 MiB / 10000 files")
    blobs = io.BytesIO(git(Path(source), "cat-file", "--batch", data=b"".join(oid + b"\n" for _, oid, _, _ in entries)))
    target.mkdir(parents=True)
    for path, oid, size, mode in entries:
        if blobs.readline().split() != [oid, b"blob", str(size).encode()]:
            raise ValueError("Unexpected snapshot object")
        content = blobs.read(size)
        if len(content) != size or blobs.read(1) != b"\n":
            raise ValueError("Incomplete snapshot object")
        file = target / path
        file.parent.mkdir(parents=True, exist_ok=True)
        file.write_bytes(content)
        file.chmod(0o755 if mode == b"100755" else 0o644)
    local_git(target, "init", "-q", "-b", "shinobi-result", "--object-format=" + ("sha256" if len(revision) == 64 else "sha1"))
    commit(target, "Selected source snapshot " + revision)
    if local_git(target, "rev-parse", "HEAD^{tree}") != git(Path(source), "rev-parse", revision + "^{tree}"):
        raise ValueError("Exported Git tree does not match the selected source commit")


def manifest(root):
    result = {}
    total = 0
    for folder, directories, files in os.walk(root, followlinks=False):
        if Path(folder) == root:
            directories[:] = [d for d in directories if d != ".git"]
        for name in [*directories, *files]:
            path = Path(folder) / name
            info = path.lstat()
            if stat.S_ISLNK(info.st_mode) or (not stat.S_ISDIR(info.st_mode) and not stat.S_ISREG(info.st_mode)):
                raise ValueError("Workspace contains a symlink or special file")
            if stat.S_ISREG(info.st_mode):
                if info.st_nlink != 1:
                    raise ValueError("Hard links are unsupported")
                total += info.st_size
                if total > MAX_SNAPSHOT_BYTES or len(result) >= 10000:
                    raise ValueError("Workspace exceeds its size limit")
                result[str(path.relative_to(root))] = (hashlib.sha256(path.read_bytes()).hexdigest(), bool(info.st_mode & 0o111))
    return result


def artifact_hash(root):
    from execution_contracts import digest
    return digest(manifest(root))


def changes(before, after):
    return sorted(path for path in before.keys() | after.keys() if before.get(path) != after.get(path))


def validate_scope(before, after, scopes):
    paths = changes(before, after)
    outside = [p for p in paths if not any(contains(s, p) for s in scopes)]
    if outside:
        raise ValueError("Scope violation: " + ", ".join(outside[:20]))
    return paths


def commit(root, message):
    # Populate the index from raw blobs. Ignore patterns, attributes and clean
    # filters must not change the artifact that verification actually observes.
    files = manifest(root)
    paths = sorted(files)
    local_git(root, "read-tree", "--empty")
    encoded = "\n".join(json.dumps(str((root / path).resolve()), ensure_ascii=False) for path in paths) + ("\n" if paths else "")
    oids = local_git(root, "hash-object", "-w", "--no-filters", "--stdin-paths", data=encoded.encode()).decode().splitlines()
    if len(oids) != len(paths):
        raise ValueError("Incomplete artifact object import")
    entries = b"".join(("100755" if files[path][1] else "100644").encode() + b" " + oid.encode() + b"\t" + path.encode() + b"\0"
                       for path, oid in zip(paths, oids))
    local_git(root, "update-index", "-z", "--index-info", data=entries)
    local_git(root, "commit", "--allow-empty", "-qm", message)
    return local_git(root, "rev-parse", "HEAD").decode().strip()


def copy_workspace(source, target):
    if target.exists():
        raise ValueError("Attempt workspace already exists; reconciliation is required")
    shutil.copytree(source, target)
    manifest(target)


def integrate(attempt, destination, before, scopes):
    after = manifest(attempt)
    paths = validate_scope(before, after, scopes)
    current = manifest(destination)
    for path in paths:
        if current.get(path) != before.get(path):
            raise ValueError("Integration conflict at " + path)
    # Copy only validated ordinary files; controller operations are not model tools.
    for path in paths:
        target = destination / path
        if path in after:
            target.parent.mkdir(parents=True, exist_ok=True)
            shutil.copy2(attempt / path, target)
        elif target.exists():
            target.unlink()
    return paths


def deliver(root, folder, source_revision):
    base = local_git(root, "rev-list", "--max-parents=0", "HEAD").decode().strip()
    patch = local_git(root, "diff", "--binary", base, "HEAD")
    (folder / "result.patch").write_bytes(patch)
    return {"workspace": str(root), "branch": "shinobi-result", "source_revision": source_revision,
            "result_revision": local_git(root, "rev-parse", "HEAD").decode().strip(),
            "artifact_hash": artifact_hash(root), "patch": str(folder / "result.patch"),
            "patch_sha256": hashlib.sha256(patch).hexdigest()}
