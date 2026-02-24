import json
import os
import sys

base_dir = os.path.abspath(os.path.join(os.path.dirname(__file__), '..', '..'))
if base_dir not in sys.path:
    sys.path.append(base_dir)

from src.utils.llm_router import get_llm

try:
    from langchain_core.prompts import PromptTemplate
    from langchain_core.output_parsers import StrOutputParser
    LANGCHAIN_AVAILABLE = True
except ImportError:
    LANGCHAIN_AVAILABLE = False

class CompositionAgent:
    """
    조합 에이전트: 
    라이브러리(사전 정의)와 방금 동적 생성된 최소 단위 컴포넌트들을 전달받아, 
    충돌(CSS 스코핑 등) 없이 하나의 매끄러운 디지털 자산(HTML 코드로 시뮬레이션) 전체를 조립해냅니다.
    """
    def __init__(self):
        self.name = "CompositionAgent"
        self.llm = get_llm(provider="openai", model_name="gpt-4o")

        if LANGCHAIN_AVAILABLE:
            self.parser = StrOutputParser()
            self.prompt = PromptTemplate(
                template=(
                    "You are an expert web layout composer.\n"
                    "You are given a list of atomic HTML component snippets and the user intent for the overall page.\n"
                    "Your task is to combine these components into a single, cohesive, responsive HTML document using Tailwind CSS.\n"
                    "Requirements:\n"
                    "- Include <!DOCTYPE html>, <html>, <head>, and <body>.\n"
                    "- Import Tailwind CSS via CDN in the <head>.\n"
                    "- Prevent CSS conflicts by ensuring proper layout scoping. Add a container wrapper (e.g., max-w-7xl, mx-auto).\n"
                    "- Structure the layout logically based on the user intent and the types of components given.\n"
                    "- Substitute generic variables (like {{title}}, {{text}}, {{placeholder}}, {{data_type}}) in the templates with context-appropriate dummy content based on the user intent.\n"
                    "- Do NOT add any markdown code block syntax (like ```html), output raw HTML directly.\n\n"
                    "User Intent: {user_intent}\n\n"
                    "Component Snippets:\n{components}\n\n"
                    "Output the full RAW HTML:"
                ),
                input_variables=["user_intent", "components"]
            )
            self.chain = self.prompt | self.llm | self.parser
        else:
            self.chain = None

    def compose(self, parsed_request: dict, component_assets: list) -> str:
        print(f"[{self.name}] 조립 시작. 대상 컴포넌트 {len(component_assets)}종을 통합합니다.")
        
        user_intent = parsed_request.get('user_intent', 'Untitled Project')
        
        if LANGCHAIN_AVAILABLE and self.chain:
            try:
                # 컴포넌트 명세와 HTML 템플릿 직렬화
                components_str = ""
                for asset in component_assets:
                    components_str += f"--- Component Name: {asset.get('name')} ---\n"
                    components_str += f"HTML Template: {asset.get('html_template')}\n\n"
                
                print(f"[{self.name}] LLM에게 풀 페이지 구성 요청...")
                response = self.chain.invoke({
                    "user_intent": user_intent,
                    "components": components_str
                })
                print(f"[{self.name}] 🟢 조립 완료. 최종 디지털 코드 생성 성공.")
                return response
            except Exception as e:
                print(f"[{self.name}] LLM 체인 실패, Fallback 하드코딩 조합 반환: {e}")
        
        # Fallback (Langchain 없거나 실패 시)
        return self._fallback_compose(parsed_request, component_assets)

    def _fallback_compose(self, parsed_request: dict, component_assets: list) -> str:
        # 기존 뼈대 로직
        final_document = """<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>AI Builder Generated Output (Fallback)</title>
    <script src="https://cdn.tailwindcss.com"></script>
    <style>
        .ai-builder-wrapper { font-family: sans-serif; }
    </style>
</head>
<body class="bg-gray-50 flex items-center justify-center min-h-screen p-4">
    <div class="ai-builder-wrapper bg-white p-6 rounded-lg shadow-xl w-full max-w-4xl flex flex-col gap-6">
"""
        user_intent = parsed_request.get('user_intent', 'Untitled Project')
        final_document += f"\n        <!-- Project Intent: {user_intent} -->\n"
        final_document += f"        <h1 class='text-2xl font-bold border-b pb-2'>{user_intent}</h1>\n"
        
        for asset in component_assets:
            rendered_html = self._render_atomic_component(asset)
            final_document += f"        <!-- Component: {asset.get('name')} -->\n"
            final_document += f"        <div class='component-container w-full'>\n"
            final_document += f"            {rendered_html}\n"
            final_document += f"        </div>\n"
            
        final_document += """
    </div>
</body>
</html>"""
        print(f"[{self.name}] (Fallback) 🟢 조립 완료. 최종 디지털 코드 생성 성공.")
        return final_document

    def _render_atomic_component(self, asset: dict) -> str:
        html = asset.get('html_template', '')
        # Fallback 용 아주 단순한 변수 채우기 방식 - {text} 든 {{text}} 든 치환
        html = html.replace('{text}', 'Submit').replace('{{text}}', 'Submit')
        html = html.replace('{title}', 'Welcome Dashboard').replace('{{title}}', 'Welcome Dashboard')
        html = html.replace('{placeholder}', 'Enter your data...').replace('{{placeholder}}', 'Enter your data...')
        html = html.replace('{data_type}', 'Revenue Over Time').replace('{{data_type}}', 'Revenue Over Time')
        html = html.replace('{param}', 'Dummy Info').replace('{{param}}', 'Dummy Info')
        return html
