import os
import json
import re

class MethodologyAgent:
    def __init__(self, config_path=None):
        self.name = "MethodologyAgent"
        if config_path is None:
            # Fallback for dynamic resolve relative to worktrees/methodology_agent/agent.py
            config_path = os.path.join(os.path.dirname(__file__), '..', '..', 'config', 'lifecycle_config.json')
            
        with open(config_path, 'r', encoding='utf-8') as f:
            self.config = json.load(f)

    def process(self, input_data):
        """
        입력된 컴포넌트 정보(주로 Generation Agent의 산출물)를 검사합니다.
        input_data: JSON 파일 경로 또는 메모리 딕셔너리
        """
        comp_data = input_data
        
        # 만약 input_data가 파일 경로라면 데이터 로드 (GenerationAgent 산출물)
        if isinstance(input_data, str) and os.path.exists(input_data):
            try:
                with open(input_data, 'r', encoding='utf-8') as f:
                    comp_data = json.load(f)
            except Exception as e:
                return {"status": "error", "message": f"QA Failed: Could not read JSON file {input_data}. {str(e)}"}

        print(f"[{self.name}] 시작: 검증 (QA) -> 데이터: {comp_data.get('component_id', 'Unknown')}")

        # GSD Rule 1: No full HTML documents. Should be a fragment.
        html_content = comp_data.get("html", "")
        if re.search(r'<\s*html\s*>', html_content, re.IGNORECASE) or re.search(r'<\s*body\s*>', html_content, re.IGNORECASE):
            print(f"[{self.name}] ❌ QA Failed: GSD Violation! HTML or BODY tags are not allowed in atomic components.")
            return {
                "status": "failed",
                "reason": "GSD Rule Violation: output must not be a full HTML document (do not include <html> or <body> tags).",
                "component_id": comp_data.get("component_id")
            }

        # Additional rules can be attached here (e.g. style scoping check, valid Tailwind class extraction check)
        
        print(f"[{self.name}] ✅ QA Passed: {comp_data.get('component_id')} is verified by GSD rules.")
        return {
            "status": "success",
            "component_id": comp_data.get("component_id"),
            "data": comp_data
        }

if __name__ == "__main__":
    # Test Methodology Agent
    agent = MethodologyAgent()
    print("Methodology Agent Instance Created.")
