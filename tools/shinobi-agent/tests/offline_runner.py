"""Test entry point only. Production runner has no fake-model switch."""
from pathlib import Path
import sys
import subprocess
from unittest.mock import patch

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from langchain_openrouter import ChatOpenRouter
from helpers import scripted_generate
import runner
import execution_api


def launch(root, run_id):
    folder = root / "runs" / run_id
    folder.mkdir(parents=True, exist_ok=True)
    with (folder / "controller.log").open("ab") as output:
        subprocess.Popen([sys.executable, str(Path(__file__).with_name("offline_execution.py")), str(root), run_id],
                         stdin=subprocess.DEVNULL, stdout=output, stderr=output, start_new_session=True)

execution_api.launch = launch

with patch.object(ChatOpenRouter, "_generate", scripted_generate):
    raise SystemExit(runner.main())
