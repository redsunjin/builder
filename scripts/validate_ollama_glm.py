#!/usr/bin/env python3
"""
Run a 10-scenario validation against the current orchestrator setup.

This script is designed for real-model checks (e.g. AI_PROVIDER=ollama,
AI_MODEL=glm-5:cloud) and records fallback/error signals from pipeline logs.
"""

import io
import json
import os
import sys
import time
from contextlib import redirect_stdout
from datetime import datetime, timezone


SCRIPT_DIR = os.path.dirname(os.path.abspath(__file__))
REPO_ROOT = os.path.abspath(os.path.join(SCRIPT_DIR, ".."))
if REPO_ROOT not in sys.path:
    sys.path.append(REPO_ROOT)

from core.orchestrator import Orchestrator


PROMPTS = [
    "헤더와 버튼, 입력창이 있는 로그인 화면 만들어줘",
    "상품 카드 3개와 상단 네비게이션이 있는 쇼핑 페이지 목업",
    "매출 그래프와 KPI 카드가 있는 대시보드",
    "사용자 프로필 페이지 레이아웃",
    "FAQ 아코디언과 문의 버튼이 있는 지원 페이지",
    "모바일 챗봇 UI 스타일의 단순 채팅 화면",
    "회원가입 폼(이메일, 비밀번호, 가입 버튼)",
    "공지사항 리스트와 상세 보기 버튼이 있는 화면",
    "푸터 포함 랜딩 페이지(히어로+CTA 버튼)",
    "검색창과 결과 카드가 있는 검색 페이지",
]


def utcnow_iso() -> str:
    return datetime.now(timezone.utc).isoformat()


def main() -> int:
    provider = os.getenv("AI_PROVIDER", "ollama")
    model_name = os.getenv("AI_MODEL", "llama3")
    print(f"[validate] provider={provider} model={model_name}")

    runtime_output_dir = os.path.abspath(
        os.getenv("RUNTIME_OUTPUT_DIR", os.path.join(REPO_ROOT, "output", "runtime"))
    )
    os.makedirs(runtime_output_dir, exist_ok=True)
    os.environ.setdefault(
        "COMPONENT_LIBRARY_PATH",
        os.path.join(runtime_output_dir, "components_validation"),
    )
    print(f"[validate] component_library={os.environ.get('COMPONENT_LIBRARY_PATH')}")

    orchestrator = Orchestrator()
    report_rows = []
    started = time.time()

    for idx, prompt in enumerate(PROMPTS, start=1):
        session_id = f"glm_validate_{idx:02d}"
        log_capture = io.StringIO()
        item = {
            "index": idx,
            "session_id": session_id,
            "prompt": prompt,
            "ok": False,
            "duration_sec": 0.0,
            "customer_fallback": False,
            "generation_fallback": False,
            "composition_fallback": False,
            "html_fallback_marker": False,
            "error": "",
        }

        started_case = time.time()
        try:
            with redirect_stdout(log_capture):
                result = orchestrator.run_pipeline(session_id, prompt)

            item["ok"] = isinstance(result, dict) and "html" in result and "metrics" in result
            if item["ok"]:
                html = result.get("html", "")
                item["html_fallback_marker"] = "Generated Output (Fallback)" in html
        except Exception as exc:
            item["error"] = f"{type(exc).__name__}: {exc}"

        logs = log_capture.getvalue()
        item["customer_fallback"] = (
            "CustomerAgent] LLM 체인 처리 실패" in logs
            or "CustomerAgent] Langchain 미설정. Mock 데이터 반환." in logs
        )
        item["generation_fallback"] = "GenerationAgent] LLM 체인 실패" in logs
        item["composition_fallback"] = "CompositionAgent] LLM 체인 실패" in logs
        item["duration_sec"] = round(time.time() - started_case, 3)
        report_rows.append(item)

        status = "ok" if item["ok"] else "fail"
        print(
            f"[{idx:02d}] {status} | customer_fb={item['customer_fallback']} "
            f"gen_fb={item['generation_fallback']} comp_fb={item['composition_fallback']} "
            f"html_fb={item['html_fallback_marker']} | {item['duration_sec']}s"
        )

    total = len(report_rows)
    ok_count = sum(1 for row in report_rows if row["ok"])
    no_fallback_count = sum(
        1
        for row in report_rows
        if row["ok"]
        and not row["customer_fallback"]
        and not row["generation_fallback"]
        and not row["composition_fallback"]
        and not row["html_fallback_marker"]
    )

    summary = {
        "timestamp_utc": utcnow_iso(),
        "provider": provider,
        "model": model_name,
        "total": total,
        "ok_count": ok_count,
        "ok_rate": round((ok_count / total) * 100, 2) if total else 0.0,
        "no_fallback_count": no_fallback_count,
        "no_fallback_rate": round((no_fallback_count / total) * 100, 2) if total else 0.0,
        "duration_total_sec": round(time.time() - started, 3),
    }

    report = {"summary": summary, "rows": report_rows}

    report_dir = os.path.join(runtime_output_dir, "validation")
    os.makedirs(report_dir, exist_ok=True)
    report_path = os.path.join(report_dir, f"glm_validation_{int(time.time())}.json")
    with open(report_path, "w", encoding="utf-8") as f:
        json.dump(report, f, ensure_ascii=False, indent=2)

    print("[validate] summary:", json.dumps(summary, ensure_ascii=False))
    print(f"[validate] report={report_path}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
