#!/usr/bin/env python3
"""Controlled test child. This never invokes a model or claims to be Deep Agents."""
import json
import sys
import time

request = json.load(sys.stdin)
query = request["query"]
if query == "FAKE_MALFORMED":
    print("not JSON")
    raise SystemExit(0)
if query == "FAKE_EMPTY":
    raise SystemExit(0)
if query == "FAKE_HANG":
    time.sleep(300)
if query == "FAKE_SLOW":
    time.sleep(0.6)
print(json.dumps({
    "request_id": request["request_id"],
    "status": "ok",
    "answer": "42",
    "model": "fake-test-only",
    "workspace": "/tmp/fake-test-only",
    "tool_calls": [],
    "received_query": query,
}))
