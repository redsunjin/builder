import json
import os
import sys

# 병렬 개발 디렉토리 경로 추가
sys.path.append(os.path.join(os.path.dirname(__file__), 'worktrees'))

from customer_agent.agent import CustomerAgent
from generation_agent.agent import GenerationAgent
from composition_agent.agent import CompositionAgent

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
            meta = self.generator.load_component_metadata(comp)
            library_assets.append(meta)
        
        # 3. Composition Agent: 원자 조각 통합 조립
        final_code = self.composer.compose(parsed_data, library_assets)
        
        # 데모용: HTML 결과물 파일로 저장
        output_file = "builder_output.html"
        with open(output_file, 'w', encoding='utf-8') as f:
            f.write(final_code)
            
        print(f"\n✅ [결과물 산출 성공] 파일 저장 완료: {output_file}")
        print("==========================================\n")
        
        return final_code

if __name__ == "__main__":
    # 모의 오버라이드: Customer Agent가 기존+동적(없는) 컴포넌트를 모두 요청하는 상황 세팅
    orchestrator = Orchestrator()
    orchestrator.customer.process_request = lambda s, u: {
        "session_id": s,
        "required_components": ["header", "custom_graph", "text_input", "button"],
        "user_intent": "대시보드 화면"
    }
    
    sample_request = "대시보드 헤더랑, 내역을 보여줄 동적 그래프 컴포넌트, 그리고 검색창(text_input), 검색버튼을 조합해줘."
    orchestrator.run_pipeline("session_dashboard", sample_request)
