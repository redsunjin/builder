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
        provider = os.getenv("CUSTOMER_LLM_PROVIDER", os.getenv("AI_PROVIDER", "ollama"))
        model_name = os.getenv("CUSTOMER_LLM_MODEL", os.getenv("AI_MODEL", "llama3"))
        self.llm = get_llm(provider=provider, model_name=model_name)
        self.allowed_component_names = self._get_allowed_component_names()
        
        if LANGCHAIN_AVAILABLE:
            self.parser = JsonOutputParser()
            self.prompt = PromptTemplate(
                template=(
                    "You are an AI assistant that analyzes user requests and extracts the required UI components.\n"
                    "Extract ONLY a valid JSON object matching the required schema. Do not include any explanations or greetings.\n"
                    "Rules:\n"
                    "- Use ONLY component identifiers from this allowlist: {allowed_components}\n"
                    "- Do NOT invent identifiers such as layout, page, screen, section, card, chart, widget, dashboard_layout.\n"
                    "- Map abstract requests to the closest allowed identifiers.\n"
                    "- Preferred mappings: chart/graph/KPI/dashboard -> custom_graph; navigation/navbar/menu -> nav_bar; login/signup/form/input -> text_input or login_form; footer -> footer_simple.\n"
                    "- Return 1 to 6 components ordered from top-to-bottom page layout.\n"
                    "- Keep user_intent short and concrete.\n"
                    "\n"
                    "Format Instructions:\n{format_instructions}\n\n"
                    "User Request:\n{user_request}\n\n"
                    "Session ID: {session_id}"
                ),
                input_variables=["user_request", "session_id"],
                partial_variables={
                    "format_instructions": self._get_format_instructions(),
                    "allowed_components": self._get_allowed_components(),
                }
            )
            self.chain = self.prompt | self.llm | self.parser
        else:
            self.chain = None

    def _get_allowed_components(self) -> str:
        return ", ".join(self._get_allowed_component_names())

    def _get_allowed_component_names(self) -> list:
        component_dirs = [
            os.path.join(os.path.dirname(__file__), '..', 'generation_agent', 'library', 'components'),
            os.path.join(os.path.dirname(__file__), '..', '..', 'output', 'components'),
        ]
        component_names = set()
        for component_dir in component_dirs:
            try:
                component_names.update(
                    file_name[:-5]
                    for file_name in os.listdir(component_dir)
                    if file_name.endswith('.json')
                )
            except Exception:
                continue
        if component_names:
            return sorted(component_names)
        return [
            "alert_banner",
            "button",
            "chat_interface",
            "custom_graph",
            "faq_accordion",
            "feature_list",
            "footer_simple",
            "header",
            "hero_section",
            "kpi_card",
            "login_form",
            "modal_dialog",
            "nav_bar",
            "notice_list",
            "pricing_table",
            "product_card",
            "profile_card",
            "search_bar",
            "testimonial_card",
            "text_input",
            "unknown_dynamic_widget",
        ]

    def _normalize_component_name(self, component_name: str) -> str:
        alias_map = {
            "chart": "custom_graph",
            "graph": "custom_graph",
            "kpi": "kpi_card",
            "kpi_card": "kpi_card",
            "card": None,
            "product_card": "product_card",
            "search_input": "search_bar",
            "searchbox": "search_bar",
            "search_box": "search_bar",
            "profile": "profile_card",
            "profile_page": "profile_card",
            "notice": "notice_list",
            "announcement": "notice_list",
            "chat": "chat_interface",
            "chatbot": "chat_interface",
            "dashboard_layout": None,
            "layout": None,
            "page": None,
            "screen": None,
            "section": None,
            "widget": None,
        }
        normalized = alias_map.get(component_name, component_name)
        if normalized in self.allowed_component_names:
            return normalized
        return None

    def _augment_components_from_request(self, user_request: str, components: list) -> list:
        lowered = user_request.lower()
        keyword_rules = [
            (("dashboard", "대시보드", "kpi", "매출"), ["custom_graph", "kpi_card"]),
            (("shopping", "shop", "상품", "쇼핑"), ["nav_bar", "product_card"]),
            (("search", "검색"), ["search_bar", "product_card"]),
            (("profile", "프로필"), ["profile_card"]),
            (("notice", "announcement", "공지"), ["notice_list"]),
            (("chat", "chatbot", "채팅"), ["chat_interface"]),
            (("faq", "자주 묻는 질문"), ["faq_accordion"]),
            (("landing", "랜딩"), ["hero_section", "button", "footer_simple"]),
            (("login", "로그인"), ["text_input", "button"]),
            (("signup", "회원가입"), ["login_form", "button"]),
        ]
        for keywords, suggested_components in keyword_rules:
            if any(keyword in lowered for keyword in keywords):
                for component_name in suggested_components:
                    if component_name in self.allowed_component_names and component_name not in components:
                        components.append(component_name)
        return components

    def _normalize_response(self, session_id: str, user_request: str, response: dict) -> dict:
        raw_components = response.get("required_components", [])
        normalized_components = []
        for component_name in raw_components:
            normalized = self._normalize_component_name(str(component_name).strip())
            if normalized and normalized not in normalized_components:
                normalized_components.append(normalized)

        normalized_components = self._augment_components_from_request(user_request, normalized_components)
        if not normalized_components:
            normalized_components = ["header", "button", "text_input"]

        return {
            "session_id": response.get("session_id") or session_id,
            "required_components": normalized_components[:6],
            "user_intent": str(response.get("user_intent") or user_request).strip()[:160],
        }

    def _get_format_instructions(self) -> str:
        interfaces_path = os.path.join(os.path.dirname(__file__), '..', '..', 'config', 'agent_interfaces.json')
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
            return self._normalize_response(session_id, user_request, response)
            
        except Exception as e:
            print(f"[{self.name}] LLM 체인 처리 실패, Fallback 동작: {e}")
            return fallback_data
