import json
import os

class CompositionAgent:
    """
    조합 에이전트: 
    라이브러리(사전 정의)와 방금 동적 생성된 최소 단위 컴포넌트들을 전달받아, 
    충돌(CSS 스코핑 등) 없이 하나의 매끄러운 디지털 자산(HTML 코드로 시뮬레이션) 전체를 조립해냅니다.
    """
    def __init__(self):
        self.name = "CompositionAgent"

    def compose(self, parsed_request: dict, component_assets: list) -> str:
        print(f"[{self.name}] 조립 시작. 대상 컴포넌트 {len(component_assets)}종을 통합합니다.")
        
        # 1. 문서 기본 스켈레톤 구성 (Tailwind 기반 CSS 스코핑 모의 지원)
        final_document = """<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>AI Builder Generated Output</title>
    <script src="https://cdn.tailwindcss.com"></script>
    <style>
        /* 글로벌 CSS 충돌 방지용 스코프 및 리셋 (모의) */
        .ai-builder-wrapper { font-family: sans-serif; }
    </style>
</head>
<body class="bg-gray-50 flex items-center justify-center min-h-screen">
    <div class="ai-builder-wrapper bg-white p-6 rounded-lg shadow-xl w-full max-w-2xl flex flex-col gap-4">
"""
        # 사용자 요구 목적 명시
        user_intent = parsed_request.get('user_intent', 'Untitled Project')
        final_document += f"\n        <!-- Project Intent: {user_intent} -->\n"
        
        # 2. 파편화된 원자 조각(Atomic Components) 결합
        for asset in component_assets:
            # LLM 호출 모방: 조각들을 문맥에 맞게 채워 넣음
            rendered_html = self._render_atomic_component(asset)
            final_document += f"        <!-- Component: {asset['name']} -->\n"
            final_document += f"        <div class='component-container w-full'>\n"
            final_document += f"            {rendered_html}\n"
            final_document += f"        </div>\n"
            
        # 3. 문서 닫기
        final_document += """
    </div>
</body>
</html>"""
        print(f"[{self.name}] 🟢 조립 완료. 최종 디지털 코드 생성 성공.")
        return final_document

    def _render_atomic_component(self, asset: dict) -> str:
        # LLM이 템플릿의 {변수}를 문맥에 맞게 채우는 과정을 시뮬레이션
        html = asset.get('html_template', '')
        # 아주 단순한 변수 채우기 방식
        if '{text}' in html: html = html.replace('{text}', 'Submit')
        if '{title}' in html: html = html.replace('{title}', 'Welcome Dashboard')
        if '{placeholder}' in html: html = html.replace('{placeholder}', 'Enter your data...')
        if '{data_type}' in html: html = html.replace('{data_type}', 'Revenue Over Time')
        
        return html
