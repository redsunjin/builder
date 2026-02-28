import atexit
import concurrent.futures
import json
import os
import signal
import sys
import threading
import time
import uuid
import weakref
from datetime import datetime, timezone

# 프로젝트 루트(core의 상위)를 sys.path에 추가하여 worktrees 내부의 모듈을 absolute path처럼 참조 가능하게 함
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from worktrees.customer_agent.agent import CustomerAgent
from worktrees.generation_agent.agent import GenerationAgent
from worktrees.composition_agent.agent import CompositionAgent
from worktrees.methodology_agent.agent import MethodologyAgent
from scripts.git_manager import GitManager

class Telemetry:
    """GSD 체계 하에서 컴포넌트 처리 효율성(토큰 절감)을 기록하는 모듈"""
    def __init__(self):
        self.total_requested = 0
        self.cache_hits = 0
        self.llm_generations = 0

    def record_hit(self):
        self.cache_hits += 1
        self.total_requested += 1

    def record_miss(self):
        self.llm_generations += 1
        self.total_requested += 1

    def get_efficiency_rate(self) -> float:
        if self.total_requested == 0: return 0.0
        return (self.cache_hits / self.total_requested) * 100

    def generate_dashboard_html(self, phase, output_path=None):
        if output_path is None:
            output_path = os.path.join(os.path.dirname(__file__), '..', 'output', 'dashboard.html')
            
        efficiency = self.get_efficiency_rate()
        html_content = f"""<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>AI Builder - Token Efficiency Dashboard</title>
    <script src="https://cdn.tailwindcss.com"></script>
</head>
<body class="bg-gray-100 p-8 font-sans text-gray-800">
    <div class="max-w-3xl mx-auto bg-white rounded-xl shadow-lg p-6">
        <h1 class="text-3xl font-bold mb-2">🚀 AI Builder Telemetry Dashboard</h1>
        <p class="text-gray-500 mb-6">Current Phase: <span class="font-semibold text-blue-600">{phase}</span></p>
        
        <div class="grid grid-cols-1 md:grid-cols-3 gap-4 mb-8">
            <div class="bg-blue-50 p-4 rounded-lg border border-blue-100 text-center">
                <div class="text-sm text-blue-500 font-bold uppercase tracking-wide">Total Components</div>
                <div class="text-4xl font-extrabold text-blue-700 mt-2">{self.total_requested}</div>
            </div>
            <div class="bg-green-50 p-4 rounded-lg border border-green-100 text-center">
                <div class="text-sm text-green-500 font-bold uppercase tracking-wide">Cache Hits (Tokens Saved)</div>
                <div class="text-4xl font-extrabold text-green-700 mt-2">{self.cache_hits}</div>
            </div>
            <div class="bg-yellow-50 p-4 rounded-lg border border-yellow-100 text-center">
                <div class="text-sm text-yellow-500 font-bold uppercase tracking-wide">LLM Generations</div>
                <div class="text-4xl font-extrabold text-yellow-700 mt-2">{self.llm_generations}</div>
            </div>
        </div>

        <div class="mb-4">
            <h2 class="text-xl font-bold mb-2">Token Savings Efficiency</h2>
            <div class="w-full bg-gray-200 rounded-full h-6 overflow-hidden">
                <div class="bg-gradient-to-r from-green-400 to-green-600 h-6 text-xs font-bold text-white text-center p-1 leading-none transition-all duration-1000" style="width: {efficiency}%">
                    {efficiency:.1f}% Cached
                </div>
            </div>
            <p class="text-sm text-gray-500 mt-2">Target savings rate: >50% (GSD Standard)</p>
        </div>
        
        <div class="mt-8 text-sm text-gray-400 border-t pt-4">
            * Dashboard updated automatically by Orchestrator.
        </div>
    </div>
</body>
</html>"""
        with open(output_path, 'w', encoding='utf-8') as f:
            f.write(html_content)
        return output_path

class Orchestrator:
    """
    생애주기 오케스트레이터: GDS 단계에 따라 에이전트들의 실행 파이프라인 제어
    이번 테스트: 동적 컴포넌트(custom_graph, text_input 등) 생성 및 통합 로직
    """
    _hooks_lock = threading.Lock()
    _instances = weakref.WeakSet()
    _hooks_registered = False
    _startup_recovery_done = False
    _startup_recovery_running = False
    _previous_signal_handlers = {}
    _last_signal = None

    def __init__(self, config_path=None):
        if config_path is None:
            config_path = os.path.join(os.path.dirname(__file__), '..', 'config', 'lifecycle_config.json')
            
        with open(config_path, 'r', encoding='utf-8') as f:
            self.config = json.load(f)
            
        self.phase = self.config['current_phase']
        self.phase_metrics = self.config['phases'][self.phase]['gate_metrics']
        
        self.customer = CustomerAgent()
        self.generator = GenerationAgent()
        self.composer = CompositionAgent()
        self.methodology = MethodologyAgent()
        
        self.repo_root = os.path.abspath(os.path.join(os.path.dirname(__file__), '..'))
        self.runtime_output_dir = os.path.abspath(
            os.getenv("RUNTIME_OUTPUT_DIR", os.path.join(self.repo_root, "output", "runtime"))
        )
        os.makedirs(self.runtime_output_dir, exist_ok=True)
        self.disable_merge_to_main = self._env_flag("ORCHESTRATOR_DISABLE_MERGE", default=False)

        self.telemetry = Telemetry()
        self.git_manager = GitManager(self.repo_root)
        self.journal_dir = os.path.join(self.runtime_output_dir, "orchestrator_runs")
        os.makedirs(self.journal_dir, exist_ok=True)

        self._state_lock = threading.Lock()
        self._active_resources = {}
        self._run_journal_paths = {}

        self._register_process_hooks()
        self._run_startup_recovery_once()

    @staticmethod
    def _env_flag(name: str, default: bool = False) -> bool:
        raw = os.getenv(name)
        if raw is None:
            return default

        normalized = str(raw).strip().lower()
        if normalized in ("1", "true", "yes", "on"):
            return True
        if normalized in ("0", "false", "no", "off"):
            return False
        return default

    @staticmethod
    def _utcnow_iso() -> str:
        return datetime.now(timezone.utc).isoformat()

    @classmethod
    def _handle_atexit(cls):
        reason = "atexit"
        if cls._last_signal is not None:
            reason = f"signal:{cls._last_signal}"

        for instance in list(cls._instances):
            instance._cleanup_all_active_resources(reason)

    @classmethod
    def _handle_signal(cls, signum, frame):
        # 신호 핸들러에서는 락을 잡는 정리 로직을 실행하지 않음.
        # 실제 정리는 run_pipeline finally 또는 atexit에서 수행된다.
        cls._last_signal = signum

        previous_handler = cls._previous_signal_handlers.get(signum)
        if callable(previous_handler) and previous_handler is not cls._handle_signal:
            previous_handler(signum, frame)
            return

        if signum == signal.SIGINT:
            raise KeyboardInterrupt
        raise SystemExit(0)

    def _register_process_hooks(self):
        with Orchestrator._hooks_lock:
            Orchestrator._instances.add(self)

            if Orchestrator._hooks_registered:
                return

            if threading.current_thread() is threading.main_thread():
                for signum in (signal.SIGINT, signal.SIGTERM):
                    Orchestrator._previous_signal_handlers[signum] = signal.getsignal(signum)
                    signal.signal(signum, Orchestrator._handle_signal)

            atexit.register(Orchestrator._handle_atexit)
            Orchestrator._hooks_registered = True

    def _run_startup_recovery_once(self):
        with Orchestrator._hooks_lock:
            if Orchestrator._startup_recovery_done:
                return
            if Orchestrator._startup_recovery_running:
                return
            Orchestrator._startup_recovery_running = True

        recovery_success = False
        try:
            self._recover_stale_worktrees()
            recovery_success = True
        finally:
            with Orchestrator._hooks_lock:
                if recovery_success:
                    Orchestrator._startup_recovery_done = True
                Orchestrator._startup_recovery_running = False

    def _write_json_atomic(self, path: str, payload: dict):
        temp_path = f"{path}.tmp"
        with open(temp_path, 'w', encoding='utf-8') as f:
            json.dump(payload, f, ensure_ascii=False, indent=2)
        os.replace(temp_path, path)

    def _create_run_id(self) -> str:
        return f"run_{int(time.time() * 1000)}_{uuid.uuid4().hex[:8]}"

    def _run_journal_path(self, run_id: str) -> str:
        return os.path.join(self.journal_dir, f"{run_id}.json")

    def _snapshot_run_resources(self, run_id: str) -> list:
        with self._state_lock:
            resources = [
                dict(resource)
                for resource in self._active_resources.values()
                if resource.get("run_id") == run_id
            ]
        resources.sort(key=lambda item: (item.get("component") or "", item.get("branch_name") or ""))
        return resources

    def _start_run_journal(self, session_id: str, user_request: str) -> str:
        run_id = self._create_run_id()
        journal_path = self._run_journal_path(run_id)
        with self._state_lock:
            self._run_journal_paths[run_id] = journal_path

        payload = {
            "run_id": run_id,
            "session_id": session_id,
            "status": "running",
            "request": user_request,
            "created_at": self._utcnow_iso(),
            "updated_at": self._utcnow_iso(),
            "finished_at": None,
            "error": None,
            "resources": [],
        }
        self._write_json_atomic(journal_path, payload)
        return run_id

    def _update_run_journal(self, run_id: str, status: str = None, error_marker: str = None, finished: bool = False):
        with self._state_lock:
            journal_path = self._run_journal_paths.get(run_id, self._run_journal_path(run_id))
            self._run_journal_paths[run_id] = journal_path

        try:
            if os.path.exists(journal_path):
                with open(journal_path, 'r', encoding='utf-8') as f:
                    payload = json.load(f)
            else:
                payload = {"run_id": run_id}
        except Exception:
            payload = {"run_id": run_id}

        payload["updated_at"] = self._utcnow_iso()
        payload["resources"] = self._snapshot_run_resources(run_id)

        if status is not None:
            payload["status"] = status
        if error_marker is not None:
            payload["error"] = error_marker
        if finished:
            payload["finished_at"] = self._utcnow_iso()

        self._write_json_atomic(journal_path, payload)

    def _build_component_resource(self, comp: str):
        branch_name = f"feat/{comp}_gen"
        worktree_path = os.path.join(self.repo_root, 'worktrees', f"temp_{comp}")
        return branch_name, worktree_path

    def _track_resource(self, run_id: str, component: str, branch_name: str, worktree_path: str):
        normalized_path = os.path.abspath(worktree_path)
        resource_key = (branch_name, normalized_path)
        resource_value = {
            "run_id": run_id,
            "component": component,
            "branch_name": branch_name,
            "worktree_path": normalized_path,
            "tracked_at": self._utcnow_iso(),
        }
        with self._state_lock:
            self._active_resources[resource_key] = resource_value
        self._update_run_journal(run_id)

    def _untrack_resource(self, branch_name: str, worktree_path: str):
        normalized_path = os.path.abspath(worktree_path)
        resource_key = (branch_name, normalized_path)
        run_id = None

        with self._state_lock:
            existing = self._active_resources.pop(resource_key, None)
            if existing:
                run_id = existing.get("run_id")

        if run_id:
            self._update_run_journal(run_id)

    def _safe_remove_resource(self, branch_name: str, worktree_path: str, context: str):
        try:
            self.git_manager.remove_worktree(worktree_path, branch_name=branch_name, force=True)
        except Exception as exc:
            print(f"[Cleanup] Warning ({context}) {branch_name}: {exc}")
        finally:
            self._untrack_resource(branch_name, worktree_path)

    def _cleanup_run_resources(self, run_id: str, reason: str):
        resources = self._snapshot_run_resources(run_id)
        if not resources:
            return

        print(f"[Cleanup] run_id={run_id}, count={len(resources)}, reason={reason}")
        for resource in resources:
            self._safe_remove_resource(
                resource.get("branch_name"),
                resource.get("worktree_path"),
                context=reason,
            )

    def _cleanup_all_active_resources(self, reason: str):
        with self._state_lock:
            run_ids = sorted({entry.get("run_id") for entry in self._active_resources.values() if entry.get("run_id")})

        for run_id in run_ids:
            self._cleanup_run_resources(run_id, f"global-{reason}")
            self._update_run_journal(
                run_id,
                status="interrupted",
                error_marker=f"Cleanup triggered by {reason}",
                finished=True,
            )

    def _recover_stale_worktrees(self):
        recovered_count = 0

        journal_dirs = []
        for candidate in (
            self.journal_dir,
            os.path.join(self.repo_root, "output", "orchestrator_runs"),
        ):
            normalized = os.path.abspath(candidate)
            if normalized not in journal_dirs and os.path.isdir(normalized):
                journal_dirs.append(normalized)

        # 1) 실행 중 상태로 남아있는 저널 기반 복구
        for journal_dir in journal_dirs:
            for file_name in sorted(os.listdir(journal_dir)):
                if not file_name.endswith(".json"):
                    continue

                journal_path = os.path.join(journal_dir, file_name)
                try:
                    with open(journal_path, 'r', encoding='utf-8') as f:
                        payload = json.load(f)
                except Exception:
                    continue

                if payload.get("status") != "running":
                    continue

                failed_resources = []
                for resource in payload.get("resources", []):
                    branch_name = resource.get("branch_name")
                    worktree_path = resource.get("worktree_path")
                    if not worktree_path:
                        continue
                    try:
                        self.git_manager.remove_worktree(worktree_path, branch_name=branch_name, force=True)
                        recovered_count += 1
                    except Exception as exc:
                        resource_copy = dict(resource)
                        resource_copy["last_error"] = str(exc)
                        failed_resources.append(resource_copy)

                if failed_resources:
                    payload["status"] = "partial_recovered"
                    payload["error"] = f"Recovered with {len(failed_resources)} resource(s) still failing cleanup."
                    payload["resources"] = failed_resources
                else:
                    payload["status"] = "recovered"
                    payload["error"] = "Recovered stale resources during startup."
                    payload["resources"] = []
                payload["updated_at"] = self._utcnow_iso()
                payload["finished_at"] = self._utcnow_iso()
                self._write_json_atomic(journal_path, payload)

        # 2) 저널에 없는 temp_* 워크트리 복구
        stale_paths = self.git_manager.cleanup_stale_temp_worktrees()
        recovered_count += len(stale_paths)

        if recovered_count:
            print(f"[Recovery] stale worktrees cleaned: {recovered_count}")

    def _resolve_worker_count(self, env_key: str, default: int) -> int:
        try:
            value = int(os.getenv(env_key, str(default)))
        except (TypeError, ValueError):
            value = default
        return max(1, value)

    def _get_agent_thread_pool_config(self) -> dict:
        return {
            "customer": self._resolve_worker_count("CUSTOMER_AGENT_THREADS", 1),
            "generation": self._resolve_worker_count("GENERATION_AGENT_THREADS", 5),
            "methodology": self._resolve_worker_count("METHODOLOGY_AGENT_THREADS", 5),
            "composition": self._resolve_worker_count("COMPOSITION_AGENT_THREADS", 1),
        }

    def _generate_component_worker(self, comp: str):
        branch_name, worktree_path = self._build_component_resource(comp)
        
        # 1. 워크트리 생성
        try:
            self.git_manager.add_worktree(branch_name, worktree_path)
        except Exception:
            pass # ignore if already exists/fails
            
        # 2. GenerationAgent 연산 수행
        file_path = os.path.join(self.generator.library_path, f"{comp}.json")
        is_hit = os.path.exists(file_path)
        
        meta = self.generator.load_component_metadata(comp)
        
        # 3. 워크트리 내에 파일 저장 및 커밋
        if os.path.exists(worktree_path):
            comp_file = os.path.join(worktree_path, f"{comp}.json")
            with open(comp_file, 'w', encoding='utf-8') as f:
                json.dump(meta, f, ensure_ascii=False, indent=2)
                
            try:
                self.git_manager.commit_changes(worktree_path, f"Generation Agent: Created {comp}")
            except Exception:
                pass # 아무 변경사항 없음
                
        return comp, meta, is_hit, branch_name, worktree_path

    def run_pipeline(self, session_id: str, user_request: str):
        run_id = self._start_run_journal(session_id, user_request)
        run_status = "failed"
        run_error = None

        print(f"\n==========================================")
        print(f"🚀 AI BUILDER 오케스트레이션 시작 [Phase: {self.phase}]")
        print(f"==========================================")
        
        try:
            thread_pool = self._get_agent_thread_pool_config()
            print(
                "[ThreadPool] "
                f"Customer={thread_pool['customer']}, "
                f"Generation={thread_pool['generation']}, "
                f"Methodology={thread_pool['methodology']}, "
                f"Composition={thread_pool['composition']}"
            )
            if self.disable_merge_to_main:
                print("[Safety] ORCHESTRATOR_DISABLE_MERGE=1 -> main 브랜치 병합 비활성화")

            with concurrent.futures.ThreadPoolExecutor(
                max_workers=thread_pool["customer"],
                thread_name_prefix="CustomerAgent",
            ) as customer_executor, concurrent.futures.ThreadPoolExecutor(
                max_workers=thread_pool["generation"],
                thread_name_prefix="GenerationAgent",
            ) as generation_executor, concurrent.futures.ThreadPoolExecutor(
                max_workers=thread_pool["methodology"],
                thread_name_prefix="MethodologyAgent",
            ) as methodology_executor:
                # 1. Customer Agent: 파싱
                parsed_data = customer_executor.submit(
                    self.customer.process_request, session_id, user_request
                ).result()
                components_needed = parsed_data["required_components"]

                for comp in components_needed:
                    branch_name, worktree_path = self._build_component_resource(comp)
                    self._track_resource(run_id, comp, branch_name, worktree_path)

                if self.phase == "Alpha" and len(components_needed) > self.phase_metrics.get("max_components_allowed", 10):
                    print(f"[Error] Alpha 단계 허용 컴포넌트 초과: {len(components_needed)}")
                    run_status = "blocked"
                    return None

                # 2. Generation + Methodology Agent: 비동기 병렬 처리
                print(f"\n⚡ [Generation Agent] {len(components_needed)}개 컴포넌트 병렬 생성 시작...")

                generation_futures = {
                    generation_executor.submit(self._generate_component_worker, comp): (index, comp)
                    for index, comp in enumerate(components_needed)
                }
                qa_futures = {}

                for generation_future in concurrent.futures.as_completed(generation_futures):
                    index, comp = generation_futures[generation_future]
                    try:
                        _, meta, is_hit, branch_name, worktree_path = generation_future.result()
                    except Exception as exc:
                        print(f"   [Error] {comp} 작업 중 예외 발생: {exc}")
                        continue

                    print(f"   [!] Methodology Agent inspecting {comp}...")
                    qa_future = methodology_executor.submit(self.methodology.process, meta)
                    qa_futures[qa_future] = (index, comp, meta, is_hit, branch_name, worktree_path)

                approved_results = []
                for qa_future in concurrent.futures.as_completed(qa_futures):
                    index, comp, meta, is_hit, branch_name, worktree_path = qa_futures[qa_future]

                    try:
                        qa_result = qa_future.result()
                    except Exception as exc:
                        qa_result = {"status": "failed", "reason": f"QA 예외: {exc}"}

                    if qa_result.get("status") == "failed":
                        print(f"   [Error] {comp} QA Failed: {qa_result.get('reason')}. Skipping merge.")
                        self._safe_remove_resource(branch_name, worktree_path, "qa-fail")
                        continue

                    approved_results.append((index, meta, branch_name, worktree_path))
                    if is_hit:
                        self.telemetry.record_hit()
                    else:
                        self.telemetry.record_miss()
                    print(f"   [+] {comp} 작업 완료 및 QA 통과 (Cache Hit: {is_hit}) | Branch: {branch_name}")

                approved_results.sort(key=lambda item: item[0])
                library_assets = [meta for _, meta, _, _ in approved_results]
                generated_branches = [(branch_name, worktree_path) for _, _, branch_name, worktree_path in approved_results]

            # 3. Composition Agent: 원자 조각 통합 조립 (Merge Master 역할 병행)
            print("\n🔄 [Composition Agent] 병합 조율 시작 (Merge Master)")
            if self.disable_merge_to_main:
                print("   [Safety] main 병합을 건너뛰고 워크트리/브랜치만 정리합니다.")
                for branch_name, worktree_path in generated_branches:
                    if branch_name and worktree_path:
                        self._safe_remove_resource(branch_name, worktree_path, "merge-disabled")
            else:
                for branch_name, worktree_path in generated_branches:
                    if branch_name and worktree_path:
                        print(f"   ⮑ Merging {branch_name}...")
                        try:
                            success, output = self.git_manager.merge_branch(branch_name, allow_unrelated=True)
                            if not success:
                                print(f"      [Warning] Merge conflict for {branch_name} - Composition Agent 개입 필요. ({output})")
                        except Exception as e:
                            print(f"      [Error] 병합 중 에러: {e}")
                        finally:
                            # 병합 완료/실패와 무관하게 워크트리 정리
                            self._safe_remove_resource(branch_name, worktree_path, "post-merge")
            
            print("\n✨ Final Layout Composition...")
            with concurrent.futures.ThreadPoolExecutor(
                max_workers=thread_pool["composition"],
                thread_name_prefix="CompositionAgent",
            ) as composition_executor:
                final_code = composition_executor.submit(
                    self.composer.compose, parsed_data, library_assets
                ).result()
            
            # 결과물 저장
            output_file = os.path.join(self.runtime_output_dir, 'builder_output.html')
            with open(output_file, 'w', encoding='utf-8') as f:
                f.write(final_code)
                
            dashboard_file = self.telemetry.generate_dashboard_html(
                self.phase,
                output_path=os.path.join(self.runtime_output_dir, "dashboard.html"),
            )
            efficiency = self.telemetry.get_efficiency_rate()
                
            print(f"\n✅ [결과물 산출 성공] 파일 저장 완료: {output_file}")
            print(f"📊 [지표 업데이트 완료] 대시보드 저장 완료: {dashboard_file}")
            print(f"   ► 토큰 절감률(Cache Hit): {efficiency:.1f}%")
            print("==========================================\n")

            run_status = "completed"
            # API 호환성을 위해 결과 코드와 메타데이터를 함께 딕셔너리로 리턴
            return {
                "html": final_code,
                "metrics": {
                    "total": self.telemetry.total_requested,
                    "hits": self.telemetry.cache_hits,
                    "misses": self.telemetry.llm_generations,
                    "efficiency": round(efficiency, 2)
                }
            }
        except BaseException as exc:
            if isinstance(exc, KeyboardInterrupt):
                run_status = "interrupted"
            run_error = f"{type(exc).__name__}: {exc}"
            print(f"[Pipeline] 예외 발생: {exc}")
            raise
        finally:
            self._cleanup_run_resources(run_id, "run-finally")
            self._update_run_journal(
                run_id,
                status=run_status,
                error_marker=run_error,
                finished=True,
            )

if __name__ == "__main__":
    orchestrator = Orchestrator()
    # GSD 검증을 위해 다양한 컴포넌트가 섞인 모의 요청
    orchestrator.customer.process_request = lambda s, u: {
        "session_id": s,
        "required_components": ["header", "nav_bar", "hero_section", "custom_graph", "text_input", "unknown_dynamic_widget", "button", "footer_simple"],
        "user_intent": "고급 엔터프라이즈 대시보드 화면"
    }
    
    sample_request = "고급 대시보드 만들어줘. 헤더, 네비, 히어로, 그래프, 텍스트입력, 알수없는위젯, 버튼, 푸터 다 넣어줘."
    orchestrator.run_pipeline("session_dashboard_gamma", sample_request)
