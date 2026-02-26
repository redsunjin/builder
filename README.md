# AI Builder Project 🚀

AI Builder는 프롬프트 한 번으로 모든 코드를 짜내는 마법 같은 도구가 아닙니다. 단일 대규모 AI 모델에게 전체 앱 생성을 맡길 때 발생하는 **막대한 토큰 비용, 환각(Hallucination), 그리고 레이아웃 충돌 문제를 현실적으로 해결하기 위한 'AI 자원 절약형 프레임워크'**입니다.

## 💡 핵심 컨셉 (Core Concept: Resource-Efficient Generation)

AI의 무분별한 토큰 낭비를 막고 결과물의 신뢰도를 높이기 위해, 대규모 단일 LLM 대신 **역할이 세분화된 하이브리드 다중 LLM 기반 에이전트 프레임워크**를 제안합니다.

1. **대화 최소화 및 정규화:** 사용자의 막연한 요청을 빠르고 저렴한 모델(Ollama 등)을 통해 명확한 부품(Component) 목록으로 파싱하여 초기 토큰 소모를 줄입니다.
2. **사전 컴포넌트 라이브러리 (토큰 극강 최적화):** 이미 만들어진 부품(예: 버튼, 헤더)은 AI에게 새로 짜게 하지 않고 DB(JSON)에서 즉시 가져옵니다. 
3. **최소 단위 동적 컴포넌트 (Atomic Generation):** 라이브러리에 없는 부품만 고성능 코딩 모델(OpenAI/Gemini)에게 "최소 단위의 HTML/Tailwind 코드 조각"으로만 렌더링하도록 강제시켜 AI 자원을 아낍니다.
4. **조립 및 결합 (Composition):** 위의 파편화된 원자 단위의 코드 조각들을, CSS 스코핑 충돌 없이 매끄러운 단일 결과물로 결합합니다.

## 🏗️ 아키텍처 및 프레임워크 (Framework Architecture)

본 프로젝트는 에이전트 병렬화(Worktree) 환경과 함께, 바이브코딩(Vibe Coding)의 **GSD(Get Stuff Done) 생애주기 관리 방법론**을 차용하여 개발되었습니다. 특히 AI 1인 개발/에이전트 협업 환경에서 컨텍스트 부패를 방지하고 실행 신뢰도를 극대화하는 GSD 철학을 오케스트레이터에 녹여냈습니다.

*   `worktrees/customer_agent`: 사용자 인터페이스 및 요구사항 JSON 파싱 전담
*   `worktrees/generation_agent`: 컴포넌트 메타(캐시) 로드 및 동적 생성 전담 (자원 절약의 핵심)
*   `worktrees/composition_agent`: 여러 컴포넌트 레이아웃 결합 전담
*   `core/orchestrator.py`: GSD 기반(컨텍스트 유지, 실행 신뢰도 확보) 및 Git Worktree 병렬 에이전트 파이프라인 제어기
*   `src/utils/llm_router.py`: 역할과 비용에 따른 다중 LLM(OpenAI, Google, Ollama) 라우터
*   `web/app.py`: 웹 서버 구동 컴포넌트 (Flask)
*   `output/`: 생성된 컴포넌트 JSON 캐시 및 최종 HTML 결과물 저장소

## 📍 진행 상태 (Roadmap & Status)

- [x] 기획 및 코어 에이전트 3종 스켈레톤 디자인 완료 
- [x] 생애주기 기반 오케스트레이션(GDS 모의) 파이프라인 연동 성공
- [x] 사전 정의 + 동적 원자 컴포넌트 결합 Mockup 테스트 완료 (**현재 Alpha 통과**)
- [x] **Phase Beta 통과:** 실제 `Langchain` 연동을 통한 하이브리드 Multi-LLM 모델 접목 및 프롬프트 고도화 완료
- [x] **Phase Gamma 통과:** UI/UX 전문가 품질 검증 및 컴포넌트 카탈로그 대량 구축 (GSD 방법론 적용) 완료
- [ ] **Phase Live 진행 중:** 실제 사용자를 위한 웹(Flask/FastAPI) 인터페이스 배포 및 지표 통합 대시보드 연동

---

> 본 README는 AI Builder 초기 뼈대(Alpha Phase) 설정과 Phase Beta(실제 LLM 연동) 계획을 간략하게 요약한 것으로, 개발 및 검증 진행에 따라 지속적으로 업데이트될 예정입니다.
