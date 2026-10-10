"""Measure trusted installed tools without executing repository code or installing dependencies."""
import hashlib
import importlib.metadata
import platform
from pathlib import Path
import shutil
import subprocess

from execution_contracts import BoundaryFailure, EnvironmentProfile, POLICY_VERSION, digest
from repository import git

LOCKFILES = {"uv.lock", "poetry.lock", "requirements.txt", "package-lock.json", "pnpm-lock.yaml",
             "yarn.lock", "Cargo.lock", "pyproject.toml", "package.json"}


def capture_environment(repository, revision, checks):
    tools = {}
    for name in sorted({"bwrap", "prlimit", "git", "python3.12", *(c.argv[0] for c in checks)}):
        resolved = shutil.which(name, path="/usr/bin:/bin")
        if not resolved:
            raise BoundaryFailure("environment", "Required system tool is unavailable: " + name)
        path = Path(resolved).resolve(strict=True)
        try:
            result = subprocess.run([str(path), "--version"], cwd="/", capture_output=True, timeout=5,
                                    env={"PATH": "/usr/bin:/bin", "HOME": "/nonexistent", "LANG": "C.UTF-8"})
            if result.returncode:
                raise ValueError("Unable to measure tool version")
            tools[name] = {"path": str(path), "sha256": hashlib.sha256(path.read_bytes()).hexdigest(),
                           "version": result.stdout.decode(errors="replace")[:2000]}
        except (OSError, subprocess.TimeoutExpired, ValueError) as exc:
            raise BoundaryFailure("environment", "Cannot fingerprint system tool " + name + ": " + str(exc)) from exc
    locks = {}
    for row in filter(None, git(Path(repository), "ls-tree", "-r", "-z", revision).split(b"\0")):
        header, raw_path = row.split(b"\t", 1)
        name = raw_path.decode()
        if Path(name).name in LOCKFILES:
            mode, kind, oid = header.split()
            if kind != b"blob" or mode not in {b"100644", b"100755"}:
                raise BoundaryFailure("environment", "Unsupported dependency metadata: " + name)
            locks[name] = oid.decode()
    details = {"policy": POLICY_VERSION, "system": platform.system(), "architecture": platform.machine(),
               "kernel": platform.release(), "tools": tools, "dependency_blobs": locks,
               "backend": {name: importlib.metadata.version(name) for name in
                           ("deepagents", "langgraph", "langchain-openrouter")},
               "network": "none", "source_mount": "read-only", "temporary_bytes": 67108864,
               "resource_limits": "per-process-prlimit-v1", "source_policy": "committed-only"}
    details["controller_files"] = {name: hashlib.sha256(Path(__file__).with_name(name).read_bytes()).hexdigest()
                                   for name in ("agent.py", "contracts.py", "runner.py", "store.py", "execution.py", "execution_api.py", "execution_store.py",
                                                "execution_contracts.py", "profiles.py", "verification.py", "workflows.py",
                                                "sandbox.py", "sandbox_fileop.py", "workspace.py", "repository.py")}
    if details["system"] != "Linux":
        raise BoundaryFailure("environment", "Only the offline Linux profile is supported")
    return EnvironmentProfile(fingerprint=digest(details), details=details)


def revalidate_environment(contract, repository):
    measured = capture_environment(repository, contract.source_revision, contract.checks)
    if measured != contract.environment:
        raise BoundaryFailure("environment", "Execution environment changed; review a new contract", amendment=True)
