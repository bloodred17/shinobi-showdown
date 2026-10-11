#!/usr/bin/env python3
"""Transport-only fixture for extension unit tests."""
import json
import sys
import time

r = json.load(sys.stdin)
q = r.get("query", "")
if q == "MALFORMED":
    print("not json"); sys.exit()
if q == "HANG":
    time.sleep(300)
if q == "SLOW":
    time.sleep(0.2)
session = {"id": r.get("session_id", "a" * 32), "repository": "/fixture", "revision": "b" * 40,
           "dirty_at_creation": False, "proposal_version": 0, "excluded_count": 0, "turn_count": 0}
result = {"version": 1, "status": "ok", "request_id": r["request_id"], "session": session}
if r["operation"] == "chat":
    result["outcome"] = {"kind": "answer", "message": q, "questions": [], "evidence": [], "proposal": None}
elif r["operation"] == "resume":
    result["history"] = []
elif r["operation"] == "list":
    result["sessions"] = [session]
elif r["operation"] == "status":
    result.update(contract=None, run=None)
elif r["operation"] == "contract":
    result["contract"] = {"hash": "c" * 64, "data": {
        "version": 1, "proposal_version": 1, "source_revision": "b" * 40,
        "model": "test/offline", "policy_version": "transport-fixture",
        "autonomy": r.get("autonomy", "standard"), "checks": [], "work_items": [],
        "proposal": {"objective": "Fixture task", "constraints": [], "exclusions": [],
                     "affected_paths": [], "acceptance_criteria": []}}}
print(json.dumps(result))
