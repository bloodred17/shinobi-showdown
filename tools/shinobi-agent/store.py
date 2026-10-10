"""Backend-owned sessions and turn outcomes, with process-safe local locking."""

from contextlib import contextmanager
import fcntl
import json
from pathlib import Path
import sqlite3
import uuid

from repository import snapshot


class Store:
    def __init__(self, root: Path):
        self.root = root.resolve()
        self.root.mkdir(parents=True, exist_ok=True, mode=0o700)
        self.db = sqlite3.connect(self.root / "sessions.sqlite", timeout=10)
        self.db.row_factory = sqlite3.Row
        self.db.executescript("""
            CREATE TABLE IF NOT EXISTS sessions (
                id TEXT PRIMARY KEY, metadata TEXT NOT NULL,
                checkpoint TEXT, reads TEXT NOT NULL DEFAULT '[]',
                proposal_version INTEGER NOT NULL DEFAULT 0,
                created_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP
            );
            CREATE TABLE IF NOT EXISTS turns (
                session_id TEXT NOT NULL, request_id TEXT NOT NULL,
                query TEXT NOT NULL, status TEXT NOT NULL,
                response TEXT, created_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP,
                PRIMARY KEY (session_id, request_id)
            );
        """)

    def close(self):
        self.db.close()

    def create(self, repository: str, revision: str) -> dict:
        session_id = uuid.uuid4().hex
        metadata = snapshot(repository, revision, self.workspace(session_id))
        with self.db:
            self.db.execute("INSERT INTO sessions(id,metadata) VALUES (?,?)", (session_id, json.dumps(metadata)))
        return self.info(session_id)

    def workspace(self, session_id: str) -> Path:
        return self.root / "sessions" / session_id / "repository"

    def row(self, session_id: str):
        row = self.db.execute("SELECT * FROM sessions WHERE id=?", (session_id,)).fetchone()
        if row is None:
            raise ValueError("Unknown session ID; use /shinobi-sessions")
        return row

    def info(self, session_id: str) -> dict:
        row = self.row(session_id)
        turns = self.db.execute("SELECT request_id,query,status,response FROM turns WHERE session_id=? ORDER BY rowid", (session_id,)).fetchall()
        # Limit transport history, never truncate the checkpoint's conversation.
        history = [dict(t) for t in turns[-20:]]
        for turn in history:
            turn["response"] = json.loads(turn["response"]) if turn["response"] else None
        return {"id": session_id, **json.loads(row["metadata"]), "proposal_version": row["proposal_version"],
                "created_at": row["created_at"], "history": history, "turn_count": len(turns)}

    def list(self) -> list[dict]:
        return [{"id": r["id"], **json.loads(r["metadata"]), "created_at": r["created_at"]}
                for r in self.db.execute("SELECT * FROM sessions ORDER BY rowid DESC LIMIT 50")]

    @contextmanager
    def locked(self, session_id: str):
        self.row(session_id)
        with (self.root / "sessions" / session_id / "lock").open("a") as lock:
            try:
                fcntl.flock(lock, fcntl.LOCK_EX | fcntl.LOCK_NB)
            except BlockingIOError as exc:
                raise ValueError("Session is busy in another process") from exc
            try:
                # A running record with no lock owner is an abandoned turn. Never replay it.
                with self.db:
                    self.db.execute("UPDATE turns SET status='interrupted',response=? WHERE session_id=? AND status='running'",
                                    (json.dumps({"kind": "error", "message": "Previous process stopped before completion. This turn was not replayed."}), session_id))
                yield
            finally:
                fcntl.flock(lock, fcntl.LOCK_UN)

    def previous(self, session_id: str, request_id: str, query: str):
        row = self.db.execute("SELECT * FROM turns WHERE session_id=? AND request_id=?", (session_id, request_id)).fetchone()
        if row and row["query"] != query:
            raise ValueError("Request ID was already used for different input")
        return row

    def begin(self, session_id, request_id, query):
        with self.db:
            self.db.execute("INSERT INTO turns(session_id,request_id,query,status) VALUES (?,?,?,'running')",
                            (session_id, request_id, query))

    def fail(self, session_id, request_id, message, status="failed"):
        with self.db:
            self.db.execute("UPDATE turns SET status=?,response=? WHERE session_id=? AND request_id=? AND status='running'",
                            (status, json.dumps({"kind": "error", "message": message}), session_id, request_id))

    def complete(self, session_id, request_id, response, checkpoint, reads):
        version = self.row(session_id)["proposal_version"]
        if response["outcome"]["kind"] == "proposal":
            version += 1
            response["proposal_version"] = version
        response["session"]["proposal_version"] = version
        with self.db:
            self.db.execute("UPDATE sessions SET checkpoint=?,reads=?,proposal_version=? WHERE id=?",
                            (json.dumps(checkpoint), json.dumps(reads), version, session_id))
            self.db.execute("UPDATE turns SET status='completed',response=? WHERE session_id=? AND request_id=?",
                            (json.dumps(response), session_id, request_id))
