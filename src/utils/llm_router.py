import json
import os
from typing import Optional, Any
from dotenv import load_dotenv

try:
    from langchain_openai import ChatOpenAI
    from langchain_google_genai import ChatGoogleGenerativeAI
    from langchain_community.chat_models import ChatOllama
    from langchain_core.language_models.chat_models import BaseChatModel
    from langchain_core.messages import AIMessage, BaseMessage
    from langchain_core.prompt_values import PromptValue
except ImportError:
    BaseChatModel = Any
    ChatOpenAI = None
    ChatGoogleGenerativeAI = None
    ChatOllama = None
    AIMessage = None
    BaseMessage = Any
    PromptValue = Any

load_dotenv()

try:
    from langchain_core.language_models.fake_chat_models import FakeListChatModel
except ImportError:
    FakeListChatModel = object

class MockLLM(FakeListChatModel):
    """API 키가 없거나 Langchain이 없을 때 동작하는 모의 객체"""
    provider: str = "mock"
    model_name: str = "mock"
    responses: list = ["Mock response"]

    def __init__(self, provider: str, model_name: str, **kwargs):
        super().__init__(responses=['{"status":"ok"}'], **kwargs)
        self.provider = provider
        self.model_name = model_name

    def _extract_prompt_text(self, input_value: Any) -> str:
        if PromptValue is not Any and isinstance(input_value, PromptValue):
            return input_value.to_string()
        if BaseMessage is not Any and isinstance(input_value, BaseMessage):
            return input_value.content
        if isinstance(input_value, list):
            return "\n".join(
                item.content if BaseMessage is not Any and isinstance(item, BaseMessage) else str(item)
                for item in input_value
            )
        return str(input_value)

    def _extract_session_id(self, prompt_text: str) -> str:
        marker = "Session ID:"
        if marker not in prompt_text:
            return "mock_session"
        return prompt_text.split(marker, 1)[1].strip().splitlines()[0].strip() or "mock_session"

    def _extract_user_request(self, prompt_text: str) -> str:
        marker = "User Request:"
        if marker not in prompt_text:
            return "Mock generated request"
        tail = prompt_text.split(marker, 1)[1]
        if "Session ID:" in tail:
            tail = tail.split("Session ID:", 1)[0]
        return tail.strip() or "Mock generated request"

    def _extract_component_name(self, prompt_text: str) -> str:
        marker = "named '"
        if marker in prompt_text:
            return prompt_text.split(marker, 1)[1].split("'", 1)[0].strip() or "mock_component"
        return "mock_component"

    def _extract_user_intent(self, prompt_text: str) -> str:
        marker = "User Intent:"
        if marker not in prompt_text:
            return "Mock generated layout"
        tail = prompt_text.split(marker, 1)[1]
        if "Component Snippets:" in tail:
            tail = tail.split("Component Snippets:", 1)[0]
        return tail.strip() or "Mock generated layout"

    def _extract_component_snippets(self, prompt_text: str) -> list:
        snippets = []
        marker = "--- Component Name: "
        for chunk in prompt_text.split(marker)[1:]:
            name, _, remainder = chunk.partition(" ---")
            snippet_marker = "HTML Template:"
            html_snippet = ""
            if snippet_marker in remainder:
                html_snippet = remainder.split(snippet_marker, 1)[1].strip().splitlines()[0].strip()
            snippets.append((name.strip(), html_snippet))
        return snippets

    def _select_components(self, request_text: str) -> list:
        lowered = request_text.lower()
        mapping = [
            (("header", "헤더"), "header"),
            (("nav", "navigation", "네비"), "nav_bar"),
            (("button", "버튼", "cta"), "button"),
            (("input", "입력", "login", "로그인", "signup", "회원가입", "form", "폼"), "text_input"),
            (("footer", "푸터"), "footer_simple"),
            (("hero", "히어로", "landing", "랜딩"), "hero_section"),
            (("chart", "graph", "대시보드", "그래프", "차트", "kpi"), "custom_graph"),
        ]
        components = []
        for keywords, component_name in mapping:
            if any(keyword in lowered for keyword in keywords):
                components.append(component_name)
        if not components:
            components = ["header", "button", "text_input"]
        return components

    def _mock_customer_response(self, prompt_text: str) -> str:
        session_id = self._extract_session_id(prompt_text)
        user_request = self._extract_user_request(prompt_text)
        payload = {
            "session_id": session_id,
            "required_components": self._select_components(user_request),
            "user_intent": user_request[:160],
        }
        return json.dumps(payload, ensure_ascii=False)

    def _mock_component_response(self, prompt_text: str) -> str:
        component_name = self._extract_component_name(prompt_text)
        component_map = {
            "button": {
                "html_template": "<button class=\"inline-flex items-center rounded-md bg-slate-900 px-4 py-2 text-sm font-medium text-white\">{text}</button>",
                "required_params": ["text"],
            },
            "text_input": {
                "html_template": "<input type=\"text\" class=\"w-full rounded-md border border-slate-300 px-3 py-2\" placeholder=\"{placeholder}\" />",
                "required_params": ["placeholder"],
            },
            "header": {
                "html_template": "<header class=\"flex items-center justify-between border-b border-slate-200 pb-4\"><div class=\"text-lg font-semibold\">{title}</div><div class=\"text-sm text-slate-500\">Navigation</div></header>",
                "required_params": ["title"],
            },
            "nav_bar": {
                "html_template": "<nav class=\"flex gap-4 text-sm text-slate-600\"><a href=\"#\">Overview</a><a href=\"#\">Features</a><a href=\"#\">Pricing</a></nav>",
                "required_params": [],
            },
            "hero_section": {
                "html_template": "<section class=\"rounded-2xl bg-slate-100 p-8\"><h1 class=\"text-3xl font-bold\">{title}</h1><p class=\"mt-2 text-slate-600\">{text}</p></section>",
                "required_params": ["title", "text"],
            },
            "custom_graph": {
                "html_template": "<div class=\"rounded-xl border border-dashed border-slate-300 bg-slate-50 p-6 text-sm text-slate-500\">Dynamic Graph Area for {data_type}</div>",
                "required_params": ["data_type"],
            },
        }
        defaults = component_map.get(
            component_name,
            {
                "html_template": f"<div class=\"rounded-lg border border-slate-200 p-4 text-sm text-slate-700\">Mock component: {component_name} ({'{'}param{'}'})</div>",
                "required_params": ["param"],
            },
        )
        payload = {
            "type": "component",
            "name": component_name,
            "html_template": defaults["html_template"],
            "required_params": defaults["required_params"],
            "description": f"Mock-generated component for {component_name}.",
        }
        return json.dumps(payload, ensure_ascii=False)

    def _fill_placeholders(self, html_snippet: str) -> str:
        replacements = {
            "{text}": "Submit",
            "{{text}}": "Submit",
            "{title}": "Mock Title",
            "{{title}}": "Mock Title",
            "{placeholder}": "Enter text",
            "{{placeholder}}": "Enter text",
            "{data_type}": "Revenue",
            "{{data_type}}": "Revenue",
            "{param}": "Value",
            "{{param}}": "Value",
        }
        for source, target in replacements.items():
            html_snippet = html_snippet.replace(source, target)
        return html_snippet

    def _mock_composition_response(self, prompt_text: str) -> str:
        user_intent = self._extract_user_intent(prompt_text)
        components = self._extract_component_snippets(prompt_text)
        rendered_sections = []
        for component_name, html_snippet in components:
            body = self._fill_placeholders(html_snippet) if html_snippet else f"<div>{component_name}</div>"
            rendered_sections.append(
                f"<section data-component=\"{component_name}\" class=\"rounded-xl border border-slate-200 bg-white p-4 shadow-sm\">{body}</section>"
            )
        joined_sections = "".join(rendered_sections) or "<section class=\"rounded-xl border border-slate-200 bg-white p-4 shadow-sm\">No components</section>"
        return (
            "<!DOCTYPE html>"
            "<html lang=\"en\">"
            "<head>"
            "<meta charset=\"UTF-8\">"
            "<meta name=\"viewport\" content=\"width=device-width, initial-scale=1.0\">"
            f"<title>{user_intent}</title>"
            "<script src=\"https://cdn.tailwindcss.com\"></script>"
            "</head>"
            "<body class=\"bg-slate-50 p-6 text-slate-900\">"
            "<main class=\"mx-auto flex max-w-5xl flex-col gap-4\">"
            f"<header class=\"mb-2\"><h1 class=\"text-2xl font-bold\">{user_intent}</h1></header>"
            f"{joined_sections}"
            "</main>"
            "</body>"
            "</html>"
        )

    def _build_response_text(self, prompt_text: str) -> str:
        if "extracts the required UI components" in prompt_text:
            return self._mock_customer_response(prompt_text)
        if "Generate a minimal, reusable HTML UI component named" in prompt_text:
            return self._mock_component_response(prompt_text)
        if "You are an expert web layout composer." in prompt_text:
            return self._mock_composition_response(prompt_text)
        return json.dumps({"status": "ok"}, ensure_ascii=False)

    def invoke(self, input: Any, config=None, *, stop=None, **kwargs) -> Any:
        prompt_text = self._extract_prompt_text(input)
        print(f"[Mock {self.provider}/{self.model_name}] LLM 호출 모방")
        response_text = self._build_response_text(prompt_text)
        if AIMessage is None:
            return response_text
        return AIMessage(content=response_text)


def _get_float_env(name: str, default: float) -> float:
    raw = os.getenv(name)
    if raw is None:
        return default
    try:
        value = float(raw)
    except (TypeError, ValueError):
        return default
    if value <= 0:
        return default
    return value


def _build_ollama_model(model_name: str):
    base_kwargs = {"model": model_name, "temperature": 0.7}
    ollama_host = os.getenv("OLLAMA_HOST")
    if ollama_host:
        base_kwargs["base_url"] = ollama_host

    timeout_seconds = _get_float_env("OLLAMA_TIMEOUT_SECONDS", 45.0)

    # ChatOllama 버전에 따라 timeout 인자명이 다를 수 있어 순차 시도
    for timeout_key in ("timeout", "request_timeout"):
        try:
            return ChatOllama(**base_kwargs, **{timeout_key: timeout_seconds})
        except TypeError:
            continue

    print("[Warning] ChatOllama timeout 인자를 지원하지 않아 기본값으로 실행합니다.")
    return ChatOllama(**base_kwargs)


def get_llm(provider: str = "ollama", model_name: str = "llama3") -> BaseChatModel:
    """
    제공자와 모델을 받아 Langchain BaseChatModel 인스턴스를 반환하는 팩토리 함수.
    `.env`에서 필요한 API 키가 없거나 라이브러리가 없는 경우 모의(Mock) 객체를 반환.
    """
    provider = provider.lower()
    
    if provider == "openai":
        api_key = os.getenv("OPENAI_API_KEY")
        if not api_key or ChatOpenAI is None:
            print(f"[Warning] OPENAI_API_KEY 없음 또는 라이브러리 미설치. Mock LLM을 반환합니다.")
            return MockLLM(provider, model_name)
        return ChatOpenAI(model=model_name, temperature=0.7)
        
    elif provider == "google":
        api_key = os.getenv("GOOGLE_API_KEY")
        if not api_key or ChatGoogleGenerativeAI is None:
            print(f"[Warning] GOOGLE_API_KEY 없음 또는 라이브러리 미설치. Mock LLM을 반환합니다.")
            return MockLLM(provider, model_name)
        return ChatGoogleGenerativeAI(model=model_name, temperature=0.7)
        
    elif provider == "ollama":
        if ChatOllama is None:
            print(f"[Warning] langchain_community 미설치. Mock LLM을 반환합니다.")
            return MockLLM(provider, model_name)
        # 로컬 Ollama 경로에서 응답 무한대기를 막기 위해 timeout을 적용
        return _build_ollama_model(model_name)
        
    else:
        print(f"[Warning] 알 수 없는 provider: {provider}. Mock LLM을 반환합니다.")
        return MockLLM(provider, model_name)
