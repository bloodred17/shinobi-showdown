"""Test entry point for detached execution; production has no scripted-model flag."""
import sys
import time
from pathlib import Path
from unittest.mock import patch

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from langchain_openrouter import ChatOpenRouter
from execution import execute_run
from execution_helpers import scripted_execution_generate


def generate(self, messages, **kwargs):
    if "--hang" in sys.argv and any("bounded, user-approved repository work item" in str(m.content) for m in messages):
        time.sleep(300)
    time.sleep(0.15)
    return scripted_execution_generate(self, messages, **kwargs)


with patch.object(ChatOpenRouter, "_generate", generate):
    execute_run(Path(sys.argv[1]), sys.argv[2])
