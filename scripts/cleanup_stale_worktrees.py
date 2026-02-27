#!/usr/bin/env python3
"""
Standalone cleanup tool for stale temp worktrees.

Features:
- Recover journals stuck in `running` state.
- Remove stale `worktrees/temp_*` worktrees.
- Support dry-run mode.
"""

import argparse
import json
import os
import sys
from datetime import datetime, timezone

SCRIPT_DIR = os.path.dirname(os.path.abspath(__file__))
if SCRIPT_DIR not in sys.path:
    sys.path.append(SCRIPT_DIR)

from git_manager import GitManager


def utcnow_iso() -> str:
    return datetime.now(timezone.utc).isoformat()


def iter_running_journals(journal_dir: str):
    if not os.path.isdir(journal_dir):
        return

    for file_name in sorted(os.listdir(journal_dir)):
        if not file_name.endswith(".json"):
            continue
        path = os.path.join(journal_dir, file_name)
        try:
            with open(path, "r", encoding="utf-8") as f:
                payload = json.load(f)
        except Exception:
            continue

        if payload.get("status") == "running":
            yield path, payload


def write_json_atomic(path: str, payload: dict):
    temp_path = f"{path}.tmp"
    with open(temp_path, "w", encoding="utf-8") as f:
        json.dump(payload, f, ensure_ascii=False, indent=2)
    os.replace(temp_path, path)


def cleanup_journal_resources(git_manager: GitManager, payload: dict, dry_run: bool) -> int:
    cleaned = 0
    failed_resources = []
    resources = payload.get("resources", [])

    for resource in resources:
        branch_name = resource.get("branch_name")
        worktree_path = resource.get("worktree_path")
        if not worktree_path:
            continue

        if dry_run:
            print(f"[dry-run] would remove {worktree_path} (branch={branch_name})")
            cleaned += 1
            continue

        try:
            git_manager.remove_worktree(worktree_path, branch_name=branch_name, force=True)
            cleaned += 1
        except Exception as exc:
            print(f"[warn] failed to remove {worktree_path}: {exc}")
            resource_copy = dict(resource)
            resource_copy["last_error"] = str(exc)
            failed_resources.append(resource_copy)

    payload["resources"] = failed_resources
    return cleaned


def list_temp_candidates(git_manager: GitManager, repo_root: str, temp_prefix: str):
    candidates = []
    for entry in git_manager.list_worktrees():
        path = entry.get("path")
        if not path:
            continue
        abspath = os.path.abspath(path)
        if abspath == repo_root:
            continue
        relpath = os.path.relpath(abspath, repo_root).replace("\\", "/")
        if relpath.startswith(temp_prefix):
            candidates.append((abspath, entry.get("branch_name")))
    return candidates


def main() -> int:
    parser = argparse.ArgumentParser(description="Cleanup stale temp worktrees and recover running journals.")
    parser.add_argument("--repo-root", default=os.path.abspath(os.path.join(SCRIPT_DIR, "..")), help="Repository root path")
    parser.add_argument("--temp-prefix", default="worktrees/temp_", help="Relative prefix used for temp worktrees")
    parser.add_argument("--dry-run", action="store_true", help="Show what would be cleaned without changing anything")
    args = parser.parse_args()

    repo_root = os.path.abspath(args.repo_root)
    journal_dir = os.path.join(repo_root, "output", "orchestrator_runs")
    git_manager = GitManager(repo_root)

    journals_seen = 0
    journal_resources_cleaned = 0

    for journal_path, payload in iter_running_journals(journal_dir):
        journals_seen += 1
        cleaned = cleanup_journal_resources(git_manager, payload, dry_run=args.dry_run)
        journal_resources_cleaned += cleaned

        if args.dry_run:
            print(f"[dry-run] would mark journal recovered: {journal_path}")
            continue

        if payload.get("resources"):
            payload["status"] = "partial_recovered"
            payload["error"] = (
                f"Recovered with {len(payload['resources'])} resource(s) still failing cleanup "
                "by cleanup_stale_worktrees.py"
            )
        else:
            payload["status"] = "recovered"
            payload["error"] = "Recovered stale resources by cleanup_stale_worktrees.py"
        payload["updated_at"] = utcnow_iso()
        payload["finished_at"] = utcnow_iso()
        write_json_atomic(journal_path, payload)
        print(f"[ok] journal updated: {journal_path} (status={payload['status']})")

    if args.dry_run:
        candidates = list_temp_candidates(git_manager, repo_root, args.temp_prefix)
        for path, branch_name in candidates:
            print(f"[dry-run] would cleanup temp worktree: {path} (branch={branch_name})")
        temp_cleaned = len(candidates)
    else:
        cleaned_paths = git_manager.cleanup_stale_temp_worktrees(temp_prefix=args.temp_prefix)
        temp_cleaned = len(cleaned_paths)
        for path in cleaned_paths:
            print(f"[ok] cleaned temp worktree: {path}")

    print(
        "summary: "
        f"journals_seen={journals_seen}, "
        f"journal_resources_cleaned={journal_resources_cleaned}, "
        f"temp_worktrees_cleaned={temp_cleaned}, "
        f"dry_run={args.dry_run}"
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
