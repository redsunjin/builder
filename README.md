# AI Builder Project 🚀

AI Builder는 프롬프트 한 번으로 모든 코드를 짜내는 마법 같은 도구가 아닙니다. 단일 대규모 AI 모델에게 전체 앱 생성을 맡길 때 발생하는 **막대한 토큰 비용, 환각(Hallucination), 그리고 레이아웃 충돌 문제를 현실적으로 해결하기 위한 'AI 자원 절약형 프레임워크'**입니다.

## 💡 핵심 컨셉 (Core Concept: Resource-Efficient Generation)

이 프로젝트가 시장에 내놓고자 하는 "UI 조립형 목업 생성기" 프로덕트(AI Builder)에 대한 구체적인 기능 정의 및 향후 비즈니스 로드맵은 다음 코어 문서를 참고하시기 바랍니다.

*   **[🎯 프로덕트 스펙 (BUILDER_SPEC.md)](./docs/BUILDER_SPEC.md)**
*   **[🛣️ 프로덕트 로드맵 (BUILDER_ROADMAP.md)](./docs/BUILDER_ROADMAP.md)**

AI의 무분별한 토큰 낭비를 막고 결과물의 신뢰도를 높이기 위해, 대규모 단일 LLM 대신 **역할이 세분화된 하이브리드 다중 LLM 기반 에이전트 프레임워크**를 제안합니다.

1. **대화 최소화 및 정규화:** 사용자의 막연한 요청을 빠르고 저렴한 모델(Ollama 등)을 통해 명확한 부품(Component) 목록으로 파싱하여 초기 토큰 소모를 줄입니다.
2. **사전 컴포넌트 라이브러리 (토큰 극강 최적화):** 이미 만들어진 부품(예: 버튼, 헤더)은 AI에게 새로 짜게 하지 않고 DB(JSON)에서 즉시 가져옵니다. 
3. **최소 단위 동적 컴포넌트 (Atomic Generation):** 라이브러리에 없는 부품만 고성능 코딩 모델(OpenAI/Gemini)에게 "최소 단위의 HTML/Tailwind 코드 조각"으로만 렌더링하도록 강제시켜 AI 자원을 아낍니다.
4. **조립 및 결합 (Composition):** 위의 파편화된 원자 단위의 코드 조각들을, CSS 스코핑 충돌 없이 매끄러운 단일 결과물로 결합합니다.

## 🏗️ 시스템 아키텍처 및 모듈 구성 (System Architecture)

본 프로젝트는 AI 자원 절약 및 결과물 정확도를 위해 각각의 역할을 분담하는 파이프라인으로 구성되어 있습니다.

*   `core/orchestrator.py`: 전체 컴포넌트 생성 및 조립 파이프라인의 핵심 제어기
*   `config/`: 생애주기 단계 및 에이전트 인터페이스 등 필수 설정 파일
*   `src/utils/llm_router.py`: 역할과 비용에 따른 다중 LLM(OpenAI, Google, Ollama) 라우터
*   `web/app.py`: 웹 서버 구동 컴포넌트 (Flask)
*   `output/`: 생성된 컴포넌트 JSON 캐시 및 최종 조립된 HTML 결과물 저장소

> **⚠️ 개발 방법론 및 팀 빌딩 가이드 (For Developers)**
> 본 프로젝트의 AI 에이전트들은 안정성 및 품질 관리(QA)를 위해 격리된 **Git Worktree 환경**에서 병렬로 개발을 진행합니다. 
> 에이전트별 구체적인 역할(Customer, Generation, Composition, QA) 및 'GSD 멀티-에이전트 방법론'에 대한 상세 가이드는 **`worktrees/README.md`** 및 `docs/GSD.md`를 참고해 주세요.

## 📍 진행 상태 (Roadmap & Status)

- [x] 기획 및 코어 에이전트 3종 스켈레톤 디자인 완료 
- [x] 생애주기 기반 오케스트레이션(GDS 모의) 파이프라인 연동 성공
- [x] 사전 정의 + 동적 원자 컴포넌트 결합 Mockup 테스트 완료 (**현재 Alpha 통과**)
- [x] **Phase Beta 통과:** 실제 `Langchain` 연동을 통한 하이브리드 Multi-LLM 모델 접목 및 프롬프트 고도화 완료
- [x] **Phase Gamma 통과:** UI/UX 전문가 품질 검증 및 컴포넌트 카탈로그 대량 구축 (GSD 방법론 적용) 완료
- [ ] **Phase Live 진행 중:** 실제 사용자를 위한 웹(Flask/FastAPI) 인터페이스 배포 및 지표 통합 대시보드 연동

---

> 본 README는 AI Builder 초기 뼈대(Alpha Phase) 설정과 Phase Beta(실제 LLM 연동) 계획을 간략하게 요약한 것으로, 개발 및 검증 진행에 따라 지속적으로 업데이트될 예정입니다.
