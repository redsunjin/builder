#!/usr/bin/env python3
"""
Configure GitHub branch protection required checks for this repository.

Default behavior:
- infer owner/repo from `origin`
- require the `no-merge-safety` check on `main`
- patch existing required status checks without overwriting unrelated settings

Use `--bootstrap-protection` only when branch protection is not enabled yet.
"""

import argparse
import json
import os
import subprocess
import sys
import urllib.error
import urllib.request


API_BASE = "https://api.github.com"
DEFAULT_CHECK = "no-merge-safety"
API_VERSION = "2022-11-28"


def get_remote_url() -> str:
    output = subprocess.check_output(
        ["git", "remote", "get-url", "origin"],
        text=True,
    )
    return output.strip()


def infer_repo_slug(remote_url: str) -> str:
    candidates = [
        "https://github.com/",
        "git@github.com:",
        "ssh://git@github.com/",
    ]
    for prefix in candidates:
        if remote_url.startswith(prefix):
            slug = remote_url[len(prefix):].strip("/")
            if slug.endswith(".git"):
                slug = slug[:-4]
            if slug.count("/") == 1:
                return slug
    raise ValueError(f"Could not infer GitHub repo from remote URL: {remote_url}")


def github_request(method: str, path: str, token: str, payload=None) -> dict:
    data = None
    if payload is not None:
        data = json.dumps(payload).encode("utf-8")

    request = urllib.request.Request(
        f"{API_BASE}{path}",
        data=data,
        method=method,
        headers={
            "Accept": "application/vnd.github+json",
            "Authorization": f"Bearer {token}",
            "X-GitHub-Api-Version": API_VERSION,
            "User-Agent": "builder-branch-protection-script",
        },
    )

    with urllib.request.urlopen(request) as response:
        raw = response.read().decode("utf-8")
        return json.loads(raw) if raw else {}


def normalize_checks(payload: dict) -> list:
    checks = []

    for item in payload.get("checks", []) or []:
        context = item.get("context")
        if context:
            checks.append(context)

    for context in payload.get("contexts", []) or []:
        if context:
            checks.append(context)

    unique = []
    seen = set()
    for check in checks:
        if check not in seen:
            unique.append(check)
            seen.add(check)
    return unique


def build_check_objects(checks: list) -> list:
    return [{"context": check} for check in checks]


def main() -> int:
    parser = argparse.ArgumentParser(
        description="Require GitHub status checks on a protected branch."
    )
    parser.add_argument(
        "--repo",
        help="GitHub repo slug (owner/repo). Defaults to inferring from origin.",
    )
    parser.add_argument(
        "--branch",
        default="main",
        help="Branch to protect. Default: main",
    )
    parser.add_argument(
        "--check",
        action="append",
        default=[],
        help=f"Required check name. May be repeated. Default: {DEFAULT_CHECK}",
    )
    parser.add_argument(
        "--strict",
        action="store_true",
        default=True,
        help="Require the branch to be up to date before merging. Default: true",
    )
    parser.add_argument(
        "--no-strict",
        dest="strict",
        action="store_false",
        help="Do not require the branch to be up to date before merging.",
    )
    parser.add_argument(
        "--bootstrap-protection",
        action="store_true",
        help="Create minimal branch protection if none exists yet.",
    )
    parser.add_argument(
        "--dry-run",
        action="store_true",
        help="Print the planned API request without sending it.",
    )
    args = parser.parse_args()

    checks = args.check or [DEFAULT_CHECK]
    repo_slug = args.repo
    if not repo_slug:
        repo_slug = infer_repo_slug(get_remote_url())

    owner, repo = repo_slug.split("/", 1)
    protection_path = f"/repos/{owner}/{repo}/branches/{args.branch}/protection"
    required_checks_path = f"{protection_path}/required_status_checks"

    print(f"[branch-protection] repo={repo_slug} branch={args.branch}")
    print(f"[branch-protection] requested_checks={checks} strict={args.strict}")

    if args.dry_run:
        print("[branch-protection] dry-run enabled; no network request sent")
        print(
            json.dumps(
                {
                    "required_checks_patch": {
                        "strict": args.strict,
                        "checks": build_check_objects(checks),
                    },
                    "bootstrap_put": {
                        "required_status_checks": {
                            "strict": args.strict,
                            "checks": build_check_objects(checks),
                        },
                        "enforce_admins": True,
                        "required_pull_request_reviews": None,
                        "restrictions": None,
                    },
                },
                ensure_ascii=False,
                indent=2,
            )
        )
        return 0

    token = os.getenv("GH_TOKEN") or os.getenv("GITHUB_TOKEN")
    if not token:
        raise SystemExit("GH_TOKEN or GITHUB_TOKEN is required.")

    try:
        current = github_request("GET", required_checks_path, token)
        merged_checks = normalize_checks(current)
        for check in checks:
            if check not in merged_checks:
                merged_checks.append(check)

        payload = {
            "strict": args.strict,
            "checks": build_check_objects(merged_checks),
        }
        updated = github_request("PATCH", required_checks_path, token, payload)
        print("[branch-protection] updated existing required status checks")
        print(json.dumps(updated, ensure_ascii=False, indent=2))
        return 0
    except urllib.error.HTTPError as exc:
        body = exc.read().decode("utf-8", errors="replace")

        if exc.code == 404 and args.bootstrap_protection:
            payload = {
                "required_status_checks": {
                    "strict": args.strict,
                    "checks": build_check_objects(checks),
                },
                "enforce_admins": True,
                "required_pull_request_reviews": None,
                "restrictions": None,
            }
            created = github_request("PUT", protection_path, token, payload)
            print("[branch-protection] created minimal branch protection")
            print(json.dumps(created, ensure_ascii=False, indent=2))
            return 0

        if exc.code == 404:
            raise SystemExit(
                "Branch protection is not enabled yet. "
                "Re-run with --bootstrap-protection or enable branch protection in GitHub first.\n"
                f"GitHub response: {body}"
            )

        raise SystemExit(f"GitHub API error {exc.code}: {body}")


if __name__ == "__main__":
    sys.exit(main())
