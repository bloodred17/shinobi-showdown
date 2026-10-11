"""Transactional approvals, operation identity, budgets, and run lifecycle."""
from contextlib import contextmanager
import fcntl
import json
import time
import uuid

from execution_contracts import BoundaryFailure, POLICY_VERSION, TaskContract, digest

TERMINAL = {"verified", "failed", "blocked", "cancelled", "waiting_approval"}


class RunStopped(Exception):
    pass


class Runs:
    def __init__(self, store):
        self.store = store
        self.db = store.db
        self.db.executescript("""
            CREATE TABLE IF NOT EXISTS contracts (
                session_id TEXT NOT NULL, version INTEGER NOT NULL,
                hash TEXT NOT NULL UNIQUE, data TEXT NOT NULL,
                PRIMARY KEY(session_id, version)
            );
            CREATE TABLE IF NOT EXISTS approvals (
                hash TEXT PRIMARY KEY, request_id TEXT NOT NULL, approved_at REAL NOT NULL
            );
            CREATE TABLE IF NOT EXISTS runs (
                id TEXT PRIMARY KEY, session_id TEXT NOT NULL,
                contract_hash TEXT NOT NULL UNIQUE, status TEXT NOT NULL,
                data TEXT NOT NULL, created_at REAL NOT NULL
            );
            CREATE TABLE IF NOT EXISTS run_events (
                seq INTEGER PRIMARY KEY AUTOINCREMENT, run_id TEXT NOT NULL,
                kind TEXT NOT NULL, data TEXT NOT NULL, created_at REAL NOT NULL
            );
            CREATE TABLE IF NOT EXISTS execution_requests (
                session_id TEXT NOT NULL, request_id TEXT NOT NULL,
                input_hash TEXT NOT NULL, response TEXT NOT NULL,
                PRIMARY KEY(session_id,request_id)
            );
            CREATE TABLE IF NOT EXISTS session_directions (
                seq INTEGER PRIMARY KEY AUTOINCREMENT, session_id TEXT NOT NULL,
                proposal_version INTEGER NOT NULL, instruction TEXT NOT NULL
            );
        """)

    def replay(self, request):
        row = self.db.execute("SELECT * FROM execution_requests WHERE session_id=? AND request_id=?",
                              (request.session_id, request.request_id)).fetchone()
        if row:
            if row["input_hash"] != digest(request.model_dump()):
                raise ValueError("Request ID was already used for different input")
            return json.loads(row["response"])

    def remember(self, request, response):
        self.db.execute("INSERT INTO execution_requests VALUES (?,?,?,?)",
                        (request.session_id, request.request_id, digest(request.model_dump()), json.dumps(response)))

    def draft(self, session_id, contract: TaskContract):
        encoded = contract.model_dump()
        identity = digest(encoded)
        self.db.execute("INSERT INTO contracts VALUES (?,?,?,?)", (session_id, contract.version, identity, json.dumps(encoded)))
        return {"hash": identity, "data": encoded}

    def latest(self, session_id):
        row = self.db.execute("SELECT * FROM contracts WHERE session_id=? ORDER BY version DESC LIMIT 1", (session_id,)).fetchone()
        return {"hash": row["hash"], "data": json.loads(row["data"])} if row else None

    def contract(self, identity):
        row = self.db.execute("SELECT * FROM contracts WHERE hash=?", (identity,)).fetchone()
        if not row:
            raise ValueError("Unknown contract")
        raw = json.loads(row["data"])
        if digest(raw) != identity:
            raise BoundaryFailure("evidence", "Contract content changed; new approval required", amendment=True)
        if raw.get("schema_version") != 2 or raw.get("policy_version") != POLICY_VERSION:
            raise BoundaryFailure("compatibility", "Legacy or unknown execution contract; records preserved, review a new contract", amendment=True)
        if not raw.get("lifecycle") or not raw.get("planning_review") or not raw.get("user_instructions"):
            raise BoundaryFailure("compatibility", "Contract predates required lifecycle planning; records preserved, review a new contract", amendment=True)
        contract = TaskContract.model_validate(raw)
        if digest(contract.model_dump()) != identity:
            raise BoundaryFailure("compatibility", "Contract is not the full canonical schema; review a new contract", amendment=True)
        return contract

    def new_run(self, session_id, identity, request_id):
        contract = self.contract(identity)
        if self.latest(session_id)["hash"] != identity or contract.proposal_version != self.store.row(session_id)["proposal_version"]:
            raise ValueError("Stale contract; review and approve the latest proposal")
        existing = self.db.execute("SELECT id FROM runs WHERE contract_hash=?", (identity,)).fetchone()
        if existing:
            return self.info(existing["id"])
        # Serialize runs in one repository; overall worker slots are enforced separately.
        repo = self.store.info(session_id)["repository"]
        for row in self.db.execute("SELECT id,session_id,status FROM runs"):
            if row["status"] not in TERMINAL and self.store.info(row["session_id"])["repository"] == repo:
                raise ValueError("Repository already has an unfinished run; settle it before approving another")
        run_id = uuid.uuid4().hex
        data = {"repair_cycle": 0, "replans": 0, "model_calls": 0, "completed": [],
                "attempts": {}, "checks": [], "reviews": [], "artifact": None,
                "invalidated": False, "message": "Approved and queued", "launch_requested": True,
                "baseline_checks": [], "failure_category": None,
                "usage": {"input_tokens": None, "output_tokens": None, "cost": None}}
        self.db.execute("INSERT INTO approvals VALUES (?,?,?)", (identity, request_id, time.time()))
        self.db.execute("INSERT INTO runs VALUES (?,?,?,?,?,?)",
                        (run_id, session_id, identity, "queued", json.dumps(data), time.time()))
        self.event(run_id, "approved", {"contract_hash": identity})
        return self.info(run_id)

    def row(self, run_id):
        row = self.db.execute("SELECT * FROM runs WHERE id=?", (run_id,)).fetchone()
        if row is None:
            raise ValueError("Unknown run ID")
        return row

    def selected(self, session_id, run_id=None):
        if run_id:
            row = self.row(run_id)
            if row["session_id"] != session_id:
                raise ValueError("Run does not belong to the selected session")
        else:
            row = self.db.execute("SELECT * FROM runs WHERE session_id=? ORDER BY created_at DESC LIMIT 1", (session_id,)).fetchone()
        return row["id"] if row else None

    def info(self, run_id):
        row = self.row(run_id)
        data = json.loads(row["data"])
        events = self.db.execute("SELECT seq,kind,data,created_at FROM run_events WHERE run_id=? ORDER BY seq DESC LIMIT 20", (run_id,)).fetchall()
        return {"id": row["id"], "session_id": row["session_id"], "contract_hash": row["contract_hash"],
                "status": row["status"], "created_at": row["created_at"], **data,
                "events": [{**dict(e), "data": json.loads(e["data"])} for e in reversed(events)]}

    def event(self, run_id, kind, data):
        self.db.execute("INSERT INTO run_events(run_id,kind,data,created_at) VALUES (?,?,?,?)",
                        (run_id, kind, json.dumps(data), time.time()))

    def update(self, run_id, *, status=None, **fields):
        # All read-modify-write paths acquire an SQLite write lock first.
        row = self.row(run_id)
        data = json.loads(row["data"])
        data.update(fields)
        self.db.execute("UPDATE runs SET status=?,data=? WHERE id=?",
                        (status or row["status"], json.dumps(data), run_id))

    @contextmanager
    def transaction(self):
        self.db.execute("BEGIN IMMEDIATE")
        try:
            yield
            self.db.commit()
        except BaseException:
            self.db.rollback()
            raise

    @contextmanager
    def lock(self, run_id):
        folder = self.store.root / "runs" / run_id
        folder.mkdir(parents=True, exist_ok=True)
        with (folder / "lock").open("a") as handle:
            try:
                fcntl.flock(handle, fcntl.LOCK_EX | fcntl.LOCK_NB)
            except BlockingIOError as exc:
                raise ValueError("Run already has a live controller") from exc
            try:
                yield
            finally:
                fcntl.flock(handle, fcntl.LOCK_UN)

    def alive(self, run_id):
        try:
            with self.lock(run_id):
                return False
        except ValueError:
            return True

    def guard(self, run_id, model_call=False):
        with self.transaction():
            info = self.info(run_id)
            contract = self.contract(info["contract_hash"])
            if info["status"] != "running" or info["invalidated"]:
                raise RunStopped("Run stopped by user control or invalidated authority")
            if not self.db.execute("SELECT 1 FROM approvals WHERE hash=?", (info["contract_hash"],)).fetchone():
                raise RunStopped("Missing approval")
            if contract.proposal_version != self.store.row(info["session_id"])["proposal_version"]:
                raise RunStopped("Proposal changed; renewed approval required")
            if time.time() - info["started_at"] > contract.limits.wall_seconds:
                raise BoundaryFailure("budget", "Approved wall-clock budget exhausted")
            if model_call:
                if info["model_calls"] >= contract.limits.model_calls:
                    raise BoundaryFailure("budget", "Approved model-call budget exhausted")
                self.update(run_id, model_calls=info["model_calls"] + 1)

    def control(self, run_id, operation, instruction=None):
        info = self.info(run_id)
        if info["status"] in TERMINAL:
            if operation in {"pause", "cancel"}:
                return info
            raise ValueError("Run is terminal; a changed task needs a new contract")
        if operation == "pause":
            self.update(run_id, status="pausing" if self.alive(run_id) else "paused", launch_requested=False)
        elif operation == "cancel":
            self.update(run_id, status="cancelling" if self.alive(run_id) else "cancelled", launch_requested=False)
        elif operation == "steer":
            if not info["invalidated"]:
                # A new instruction invalidates the old proposal even if model generation later fails.
                self.db.execute("UPDATE sessions SET proposal_version=proposal_version+1 WHERE id=?", (info["session_id"],))
            self.db.execute("INSERT INTO session_directions(session_id,proposal_version,instruction) VALUES (?,?,?)",
                            (info["session_id"], self.store.row(info["session_id"])["proposal_version"], instruction or ""))
            self.update(run_id, status="pausing" if self.alive(run_id) else "waiting_approval", invalidated=True,
                        launch_requested=False, message="Direction changed; draft and approve a new contract before execution")
        elif operation in {"continue", "recover"}:
            if info["invalidated"]:
                raise ValueError("Authority invalidated; approve a new contract")
            if self.alive(run_id):
                raise ValueError("Controller is still active; wait for it to settle")
            if info["status"] not in {"paused", "interrupted", "running", "queued", "pausing"}:
                raise ValueError("Run cannot be resumed")
            self.update(run_id, status="queued", launch_requested=True)
        self.event(run_id, operation, {"instruction": instruction} if instruction else {})
        return self.info(run_id)
