# AI Builder Project 🚀

AI Builder는 비개발자나 기획자 등 누구나 자연어 요구사항만 입력하면, **가장 빠르고 저렴하게 시안, 디자인 가이드, 앱, AI 스킬 등의 디지털 자산을 자동 생성**해 주는 시스템입니다.

## 💡 핵심 컨셉 (Core Concept)

단일 대규모 AI 모델이 전체 코드를 한 번에 짜게 하는 기존 방식의 한계(높은 토큰 비용, 떨어지는 퀄리티, 레이아웃 충돌)를 극복하기 위해 제안된 **하이브리드 다중 LLM 기반 전문 에이전트 프레임워크**입니다.

1. **대화 최소화 및 정규화:** 사용자의 막연한 요청을 빠르고 저렴한 모델(Ollama 등)을 통해 명확한 부품(Component) 목록으로 파싱합니다.
2. **사전 컴포넌트 라이브러리 (토큰 최적화):** 이미 만들어진 부품(예: 버튼, 헤더)은 DB(JSON)에서 즉시 가져옵니다. 
3. **최소 단위 동적 컴포넌트 (Atomic Generation):** 라이브러리에 없는 부품만 고성능 코딩 모델(OpenAI/Gemini)에게 "최소 단위의 HTML/Tailwind 코드 조각"으로 동적 생성시킵니다.
4. **조립 및 결합 (Composition):** 위의 파편화된 원자 단위의 코드 조각들을, CSS 스코핑 충돌 없이 매끄러운 단일 결과물로 결합합니다.

## 🏗️ 아키텍처 및 프레임워크 (Framework Architecture)

본 프로젝트는 영국 GDS(Government Digital Service) 생애주기 관리 방법론과 강력한 에이전트 병렬화(Worktree) 방식을 차용하여 개발되었습니다.

*   `worktrees/customer_agent`: 사용자 인터페이스 및 요구사항 JSON 파싱 전담
*   `worktrees/generation_agent`: 컴포넌트 정보(캐시) 로드 및 동적 생성 전담
*   `worktrees/composition_agent`: 여러 컴포넌트 레이아웃 결합 전담
*   `orchestrator.py`: 각 GDS Phase(Alpha/Beta)의 목표 통과(Gate) 기준을 통제하는 메인 파이프라인
*   `utils/llm_router.py`: 역할과 비용에 따른 다중 LLM(OpenAI, Google, Ollama) 라우터 (예정)

## 📍 진행 상태 (Roadmap & Status)

- [x] 기획 및 코어 에이전트 3종 스켈레톤 디자인 완료 
- [x] 생애주기 기반 오케스트레이션(GDS 모의) 파이프라인 연동 성공
- [x] 사전 정의 + 동적 원자 컴포넌트 결합 Mockup 테스트 완료 (**현재 Alpha 통과**)
- [ ] **Phase Beta 진행 중:** 실제 `Langchain` 연동을 통한 하이브리드 Multi-LLM 모델 접목 및 프롬프트 고도화
- [ ] UI/UX 전문가 품질 검증 및 컴포넌트 카탈로그 대량 구축
- [ ] 라이브 베포 및 VC 향 비즈니스 효율성(토큰 최적화 지표) 시각화 대시보드 연동

---

> 본 README는 AI Builder 초기 뼈대(Alpha Phase) 설정과 Phase Beta(실제 LLM 연동) 계획을 간략하게 요약한 것으로, 개발 및 검증 진행에 따라 지속적으로 업데이트될 예정입니다.
