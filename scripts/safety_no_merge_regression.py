#!/usr/bin/env python3
"""
Safety regression test for merge-disabled orchestrator runs.

Checks:
1) run_pipeline returns API-compatible payload.
2) main HEAD does not change when ORCHESTRATOR_DISABLE_MERGE=1.
3) temp worktrees are cleaned up after completion.
"""

import argparse
import os
import subprocess
import sys
import time


SCRIPT_DIR = os.path.dirname(os.path.abspath(__file__))
REPO_ROOT = os.path.abspath(os.path.join(SCRIPT_DIR, ".."))
if REPO_ROOT not in sys.path:
    sys.path.append(REPO_ROOT)

from core.orchestrator import Orchestrator
from scripts.git_manager import GitManager


def get_head_sha(repo_root: str) -> str:
    output = subprocess.check_output(
        ["git", "rev-parse", "HEAD"],
        cwd=repo_root,
        text=True,
    )
    return output.strip()


def list_temp_worktrees(git_manager: GitManager) -> list:
    items = []
    for entry in git_manager.list_worktrees():
        path = entry.get("path")
        if not path:
            continue
        rel = os.path.relpath(os.path.abspath(path), REPO_ROOT).replace("\\", "/")
        if rel.startswith("worktrees/temp_"):
            items.append(path)
    return sorted(items)


def main() -> int:
    parser = argparse.ArgumentParser(
        description="Regression test: merge-disabled run must not change main HEAD."
    )
    parser.add_argument(
        "--intent",
        default="헤더와 버튼, 입력창이 있는 간단한 로그인 UI",
        help="User intent used for pipeline run",
    )
    parser.add_argument(
        "--provider",
        default=os.getenv("AI_PROVIDER", "openai"),
        help="LLM provider for this regression run",
    )
    parser.add_argument(
        "--model",
        default=os.getenv("AI_MODEL", "gpt-4o"),
        help="LLM model for this regression run",
    )
    args = parser.parse_args()

    os.environ["ORCHESTRATOR_DISABLE_MERGE"] = "1"
    os.environ["AI_PROVIDER"] = args.provider
    os.environ["AI_MODEL"] = args.model

    runtime_output_dir = os.path.abspath(
        os.getenv("RUNTIME_OUTPUT_DIR", os.path.join(REPO_ROOT, "output", "runtime"))
    )
    os.makedirs(runtime_output_dir, exist_ok=True)
    os.environ.setdefault(
        "COMPONENT_LIBRARY_PATH",
        os.path.join(runtime_output_dir, "components_safety_regression"),
    )

    print(
        "[safety] provider="
        f"{os.environ['AI_PROVIDER']} model={os.environ['AI_MODEL']} "
        f"ORCHESTRATOR_DISABLE_MERGE={os.environ['ORCHESTRATOR_DISABLE_MERGE']}"
    )
    print(f"[safety] component_library={os.environ.get('COMPONENT_LIBRARY_PATH')}")

    git_manager = GitManager(REPO_ROOT)
    head_before = get_head_sha(REPO_ROOT)
    before_temp = list_temp_worktrees(git_manager)
    if before_temp:
        print(f"[warn] existing temp worktrees before run: {before_temp}")

    session_id = f"safety_no_merge_{int(time.time())}"
    orchestrator = Orchestrator()
    result = orchestrator.run_pipeline(session_id, args.intent)

    if not isinstance(result, dict) or "html" not in result or "metrics" not in result:
        raise RuntimeError("run_pipeline did not return expected API payload (html + metrics).")

    head_after = get_head_sha(REPO_ROOT)
    if head_after != head_before:
        raise RuntimeError(
            "HEAD changed while merge was disabled. "
            f"before={head_before} after={head_after}"
        )

    after_temp = list_temp_worktrees(git_manager)
    if after_temp:
        raise RuntimeError(f"temp worktrees remain after run: {after_temp}")

    print("[ok] safety regression passed")
    print(f"[ok] head_before={head_before} head_after={head_after}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
