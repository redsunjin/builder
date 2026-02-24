import json
import os

class CustomerAgent:
    """
    고객 에이전트: 요청 텍스트를 파싱하여 필요한 컴포넌트 목록만 추출합니다 (대화 최소화).
    Interface: CustomerToComposition (JSON Schema)
    """
    def __init__(self):
        self.name = "CustomerAgent"

    def process_request(self, session_id: str, user_request: str) -> dict:
        print(f"[{self.name}] 분석 중: {user_request}")
        # MVP Mocking 로직: 요구사항에서 필요 컴포넌트를 하드코딩으로 추출
        return {
            "session_id": session_id,
            "required_components": ["header", "button", "text_input"],
            "user_intent": "Create a simple login form"
        }
