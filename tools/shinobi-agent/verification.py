"""Protected check inputs, baseline observations and independently measured outcomes."""
import hashlib
import re
from pathlib import Path

from execution_contracts import BoundaryFailure, contains, digest, scope_path
from repository import git, safe_path
from sandbox import Sandbox
from workspace import artifact_hash, manifest

CONFIG_NAMES = {"pyproject.toml", "pytest.ini", "tox.ini", "setup.cfg", "conftest.py", "unittest.py",
                "package.json", "package-lock.json", "Cargo.toml", "Cargo.lock", "uv.lock"}


def oracle_file(path):
    name = Path(path).name
    return (name in CONFIG_NAMES or name.startswith("test_") or name.endswith(("_test.py", ".test.ts", ".spec.ts")) or
            any(part in {"tests", "test", "spec", "__tests__"} for part in Path(path).parts) or
            name.startswith(("jest.config.", "vitest.config.", "vite.config.")))


def capture_protection(repository, revision, checks):
    blobs = {}
    for row in filter(None, git(Path(repository), "ls-tree", "-r", "-z", revision).split(b"\0")):
        header, raw_path = row.split(b"\t", 1)
        mode, kind, oid = header.split()
        path = safe_path(raw_path.decode())
        if kind == b"blob" and mode in {b"100644", b"100755"}:
            blobs[path] = (oid, mode == b"100755")
    selected = set()
    for check in checks:
        if check.protected_paths is None:
            paths = sorted(path for path in blobs if oracle_file(path))
            check.protected_paths = paths
        else:
            paths = []
            for scope in check.protected_paths:
                scope_path(scope)
                found = [path for path in blobs if contains(scope, path)]
                if not found:
                    raise BoundaryFailure("evidence", "Protected check input is absent from the source baseline: " + scope)
                paths.extend(found)
            check.protected_paths = sorted(set(paths))
        # Inline command expectations are already immutable contract inputs. A
        # repository-based check must bind at least one independently protected input.
        inline = check.argv[0].startswith("python3") and "-c" in check.argv
        if not paths and not inline:
            raise BoundaryFailure("evidence", "Declare protected_paths for repository check " + check.id)
        selected.update(paths)
    if len(selected) > 1000:
        raise BoundaryFailure("evidence", "Protected check inputs exceed the 1000-file review limit")
    return {path: (hashlib.sha256(git(Path(repository), "cat-file", "blob", blobs[path][0].decode())).hexdigest(), blobs[path][1])
            for path in sorted(selected)}


def validate_protection(contract, workspace):
    actual = manifest(workspace)
    changed = [path for path, expected in contract.protected_inputs.items() if actual.get(path) != expected]
    if changed:
        raise BoundaryFailure("evidence", "Protected check inputs changed: " + ", ".join(changed[:20]), amendment=True)


def execute_checks(context, contract, workspace, phase):
    validate_protection(contract, workspace)
    identity = artifact_hash(workspace)
    sandbox = Sandbox(workspace, context.guard)
    results = []
    for check in contract.checks:
        context.guard()
        category, outcome = None, "passed"
        try:
            result = sandbox.execute(check.argv, cwd=check.cwd, timeout=check.timeout_seconds)
            if result["exit_code"] != check.expected_exit_code:
                category, outcome = "code", "failed"
                if result["stderr"].startswith("bwrap:") or (phase == "baseline" and "ModuleNotFoundError" in result["stderr"]):
                    category = "environment"
        except TimeoutError as exc:
            result = {"argv": check.argv, "cwd": check.cwd, "exit_code": -1,
                      "stdout": "", "stderr": str(exc), "seconds": check.timeout_seconds}
            category, outcome = "code", "timeout"
        except RuntimeError as exc:
            result = {"argv": check.argv, "cwd": check.cwd, "exit_code": -1,
                      "stdout": "", "stderr": str(exc), "seconds": 0}
            category, outcome = "environment", "unavailable"
        test_count = None
        if "-m" in check.argv and "unittest" in check.argv:
            output = result["stdout"] + "\n" + result["stderr"]
            counts = re.findall(r"(?m)^Ran (\d+) tests? in ", output)
            test_count = int(counts[-1]) if counts else None
            if (category is None and test_count is None) or (category != "environment" and (
                    test_count == 0 or re.search(r"\bskipped=\d+", output))):
                category, outcome = "evidence", "missing_or_skipped_tests"
            baseline = next((row for row in context.info().get("baseline_checks", []) if row["id"] == check.id), None)
            if phase == "candidate" and category is None and baseline and baseline.get("test_count") and test_count < baseline["test_count"]:
                category, outcome = "evidence", "reduced_test_count"
        result.update(id=check.id, artifact_hash=identity, phase=phase, environment=contract.environment.model_dump(),
                      protected_inputs_hash=digest(contract.protected_inputs), expected_exit_code=check.expected_exit_code,
                      outcome=outcome, failure_category=category, test_count=test_count)
        results.append(result)
        context.event("baseline_check" if phase == "baseline" else "verification", result)
    validate_protection(contract, workspace)
    if artifact_hash(workspace) != identity:
        raise BoundaryFailure("evidence", "Artifact changed during verification", amendment=True)
    return results


def require_available(results):
    failed = next((result for result in results if result["failure_category"] in {"environment", "evidence"}), None)
    if failed:
        raise BoundaryFailure(failed["failure_category"], "Check " + failed["id"] + " cannot establish required evidence: " + failed["stderr"][-1500:])
