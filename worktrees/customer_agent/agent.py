import json
import os
import sys

# src 
base_dir = os.path.abspath(os.path.join(os.path.dirname(__file__), '..', '..'))
if base_dir not in sys.path:
    sys.path.append(base_dir)

from src.utils.llm_router import get_llm

try:
    from langchain_core.prompts import PromptTemplate
    from langchain_core.output_parsers import JsonOutputParser
    LANGCHAIN_AVAILABLE = True
except ImportError:
    LANGCHAIN_AVAILABLE = False

class CustomerAgent:
    """
    고객 에이전트: 요청 텍스트를 파싱하여 필요한 컴포넌트 목록만 추출합니다 (대화 최소화).
    Interface: CustomerToComposition (JSON Schema)
    """
    def __init__(self):
        self.name = "CustomerAgent"
        self.llm = get_llm(provider="ollama", model_name="llama3")
        
        if LANGCHAIN_AVAILABLE:
            self.parser = JsonOutputParser()
            self.prompt = PromptTemplate(
                template=(
                    "You are an AI assistant that analyzes user requests and extracts the required UI components.\n"
                    "Extract ONLY a valid JSON object matching the required schema. Do not include any explanations or greetings.\n"
                    "\n"
                    "Format Instructions:\n{format_instructions}\n\n"
                    "User Request:\n{user_request}\n\n"
                    "Session ID: {session_id}"
                ),
                input_variables=["user_request", "session_id"],
                partial_variables={"format_instructions": self._get_format_instructions()}
            )
            self.chain = self.prompt | self.llm | self.parser
        else:
            self.chain = None

    def _get_format_instructions(self) -> str:
        interfaces_path = os.path.join(os.path.dirname(__file__), '..', '..', 'interfaces', 'agent_interfaces.json')
        try:
            with open(interfaces_path, 'r', encoding='utf-8') as f:
                schema = json.load(f)
                return json.dumps(schema.get("CustomerToComposition", {}), indent=2)
        except Exception:
            return '{"session_id": "string", "required_components": ["string"], "user_intent": "string"}'

    def process_request(self, session_id: str, user_request: str) -> dict:
        print(f"[{self.name}] 분석 중: {user_request}")
        
        # 기본 폴백 데이터 (MVP Mocking)
        fallback_data = {
            "session_id": session_id,
            "required_components": ["header", "button", "text_input"],
            "user_intent": "Create a simple login form"
        }

        if not LANGCHAIN_AVAILABLE or not self.chain:
            print(f"[{self.name}] Langchain 미설정. Mock 데이터 반환.")
            return fallback_data
            
        try:
            # 실제 LLM 호출 (모의 객체일 경우 mock 객체가 처리됨)
            response = self.chain.invoke({"user_request": user_request, "session_id": session_id})
            return response
            
        except Exception as e:
            print(f"[{self.name}] LLM 체인 처리 실패, Fallback 동작: {e}")
            return fallback_data
