import json
import os
import sys

# 병렬 개발 디렉토리 경로 추가
sys.path.append(os.path.join(os.path.dirname(__file__), 'worktrees'))

from customer_agent.agent import CustomerAgent
from generation_agent.agent import GenerationAgent
from composition_agent.agent import CompositionAgent

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

        # 2. Generation Agent: 라이브러리 메타데이터 확보 및 없으면 '동적 생성(LLM)'
        library_assets = []
        for comp in components_needed:
            # Telemetry 추적을 위해 캐시 유무 선별 (GenerationAgent 로직을 살짝 래핑)
            file_path = os.path.join(self.generator.library_path, f"{comp}.json")
            if os.path.exists(file_path):
                self.telemetry.record_hit()
            else:
                self.telemetry.record_miss()
                
            meta = self.generator.load_component_metadata(comp)
            library_assets.append(meta)
        
        # 3. Composition Agent: 원자 조각 통합 조립
        final_code = self.composer.compose(parsed_data, library_assets)
        
        # 결과물 저장
        output_file = "builder_output.html"
        with open(output_file, 'w', encoding='utf-8') as f:
            f.write(final_code)
            
        dashboard_file = self.telemetry.generate_dashboard_html(self.phase)
            
        print(f"\n✅ [결과물 산출 성공] 파일 저장 완료: {output_file}")
        print(f"📊 [지표 업데이트 완료] 대시보드 저장 완료: {dashboard_file}")
        print(f"   ► 토큰 절감률(Cache Hit): {self.telemetry.get_efficiency_rate():.1f}%")
        print("==========================================\n")
        
        return final_code

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
