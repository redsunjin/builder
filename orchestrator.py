import json
import os
import sys
import concurrent.futures

# 병렬 개발 디렉토리 경로 추가
sys.path.append(os.path.join(os.path.dirname(__file__), 'worktrees'))

from customer_agent.agent import CustomerAgent
from generation_agent.agent import GenerationAgent
from composition_agent.agent import CompositionAgent
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

    def generate_dashboard_html(self, phase, output_path="dashboard.html"):
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
    def __init__(self, config_path="lifecycle_config.json"):
        with open(config_path, 'r', encoding='utf-8') as f:
            self.config = json.load(f)
            
        self.phase = self.config['current_phase']
        self.phase_metrics = self.config['phases'][self.phase]['gate_metrics']
        
        self.customer = CustomerAgent()
        self.generator = GenerationAgent()
        self.composer = CompositionAgent()
        
        self.telemetry = Telemetry()
        self.git_manager = GitManager(os.path.dirname(__file__))

    def _generate_component_worker(self, comp: str):
        branch_name = f"feat/{comp}_gen"
        worktree_path = os.path.join(os.path.dirname(__file__), 'worktrees', f"temp_{comp}")
        
        # 1. 워크트리 생성
        try:
            self.git_manager.add_worktree(branch_name, worktree_path)
        except Exception as e:
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
        print(f"\n==========================================")
        print(f"🚀 AI BUILDER 오케스트레이션 시작 [Phase: {self.phase}]")
        print(f"==========================================")
        
        # 1. Customer Agent: 파싱 (업데이트된 시나리오)
        parsed_data = self.customer.process_request(session_id, user_request)
        components_needed = parsed_data['required_components']
        
        if self.phase == "Alpha" and len(components_needed) > self.phase_metrics.get('max_components_allowed', 10):
            print(f"[Error] Alpha 단계 허용 컴포넌트 초과: {len(components_needed)}")
            return None

        # 2. Generation Agent: 비동기 병렬(Parallel) Worktree 기반 생성
        library_assets = []
        generated_branches = []
        print(f"\n⚡ [Generation Agent] {len(components_needed)}개 컴포넌트 병렬 생성 시작...")
        
        with concurrent.futures.ThreadPoolExecutor(max_workers=5) as executor:
            future_to_comp = {executor.submit(self._generate_component_worker, comp): comp for comp in components_needed}
            for future in concurrent.futures.as_completed(future_to_comp):
                comp = future_to_comp[future]
                try:
                    res_comp, meta, is_hit, branch_name, worktree_path = future.result()
                    library_assets.append(meta)
                    generated_branches.append((branch_name, worktree_path))
                    
                    if is_hit:
                        self.telemetry.record_hit()
                    else:
                        self.telemetry.record_miss()
                    print(f"   [+] {comp} 작업 완료 (Cache Hit: {is_hit}) | Branch: {branch_name}")
                except Exception as exc:
                    print(f"   [Error] {comp} 작업 중 예외 발생: {exc}")

        # 3. Composition Agent: 원자 조각 통합 조립 (Merge Master 역할 병행)
        print("\n🔄 [Composition Agent] 병합 조율 시작 (Merge Master)")
        for branch_name, worktree_path in generated_branches:
            if branch_name and worktree_path:
                print(f"   ⮑ Merging {branch_name}...")
                try:
                    success, output = self.git_manager.merge_branch(branch_name, allow_unrelated=True)
                    if not success:
                        print(f"      [Warning] Merge conflict for {branch_name} - Composition Agent 개입 필요. ({output})")
                except Exception as e:
                    print(f"      [Error] 병합 중 에러: {e}")
                
                # 병합 완료 후 워크트리 정리
                self.git_manager.remove_worktree(worktree_path, branch_name)
        
        print("\n✨ Final Layout Composition...")
        final_code = self.composer.compose(parsed_data, library_assets)
        
        # 결과물 저장
        output_file = "builder_output.html"
        with open(output_file, 'w', encoding='utf-8') as f:
            f.write(final_code)
            
        dashboard_file = self.telemetry.generate_dashboard_html(self.phase)
        efficiency = self.telemetry.get_efficiency_rate()
            
        print(f"\n✅ [결과물 산출 성공] 파일 저장 완료: {output_file}")
        print(f"📊 [지표 업데이트 완료] 대시보드 저장 완료: {dashboard_file}")
        print(f"   ► 토큰 절감률(Cache Hit): {efficiency:.1f}%")
        print("==========================================\n")
        
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
