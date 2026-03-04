import os
from typing import Optional, Any
from dotenv import load_dotenv

try:
    from langchain_openai import ChatOpenAI
    from langchain_google_genai import ChatGoogleGenerativeAI
    from langchain_community.chat_models import ChatOllama
    from langchain_core.language_models.chat_models import BaseChatModel
except ImportError:
    BaseChatModel = Any
    ChatOpenAI = None
    ChatGoogleGenerativeAI = None
    ChatOllama = None

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
        # 모의 JSON 응답을 반환하도록 설정
        mock_json_response = '''{
            "session_id": "mock_session",
            "required_components": ["header", "button", "text_input", "footer_simple"],
            "user_intent": "mocked intent from router"
        }'''
        super().__init__(responses=[mock_json_response], **kwargs)
        self.provider = provider
        self.model_name = model_name

    def invoke(self, prompt: str, **kwargs) -> Any:
        print(f"[Mock {self.provider}/{self.model_name}] LLM 호출 모방")
        return super().invoke(prompt, **kwargs)


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
