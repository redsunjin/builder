# AI Builder Team Building & Development Methodology

이 문서는 AI Builder 프로젝트 자체를 개발/고도화하기 위한 **멀티-에이전트 시스템 구조 및 Git Worktree 기반 개발 방법론** 가이드입니다. 

AI Builder 프로덕트에 대한 전반적인 소개는 [Root README.md](../README.md)를 참고하세요.

## 👥 팀 빌딩 (The Multi-Agent Team)

AI Builder 내부의 에이전트들은 단일 컨텍스트에 의존하지 않고, 각자의 특화된 역할을 가진 별도의 담당자처럼 행동합니다.

*   **`customer_agent` (기획/분석가):** 
    *   사용자의 모호한 텍스트 요구사항을 분석하여 명확한 컴포넌트 명세서(JSON)로 파싱합니다. 전체 파이프라인의 시작점 역할을 합니다.
*   **`methodology_agent` (프로젝트/QA 매니저):** 
    *   프로젝트의 방법론 통제와 산출물 품질을 관리합니다. 컴포넌트가 조립되기 전 개입하여 GSD 원칙(원자성 강제, HTML/BODY 태그 금지 등)을 위반했는지 정적 검사(QA)를 수행하고 반려하거나 통과시킵니다.
*   **`generation_agent` (AI 코더):** 
    *   요청받은 최소 단위의 컴포넌트(Atomic Component)를 동적으로 생성합니다. (비용 최적화를 위해 캐시 라이브러리를 우선 조횝니다).
*   **`composition_agent` (아키텍트/퍼블리셔):** 
    *   매니저(Methodology)의 QA 검증을 통과한 파편화된 컴포넌트 코드 조각들만 취합하여, 하나의 완성된 페이지 레이아웃으로 병합합니다.

## 🏗️ Git Worktrees 병렬 방법론 (GSD Workflow)

이 프로젝트는 컨텍스트가 오염되는 것을 극도로 경계하는 **GSD(Get Stuff Done) 철학**을 따릅니다. 무거운 단일 프롬프트를 지양하고, 다수의 컴포넌트가 완전히 독립된 작업 환경에서 병렬로 안전하게 생성되도록 설계되었습니다.

1.  **할당 및 격리 (Worktree Creation):** 
    컴포넌트 생성이 필요할 때, 오케스트레이터(`core/orchestrator.py`)는 현재의 메인 브랜치가 아닌 격리된 `worktrees/temp_X` 임시 폴더와 신규 토픽 브랜치(`feat/X_gen`)를 파생시킵니다.
2.  **동시 작업 (Parallel Generation):** 
    `GenerationAgent` 모듈들이 각각의 템프 워크트리에 접속하여 완벽히 고립된 상태(Clean Context)로 코드를 짜고 독립 커밋을 기록합니다.
3.  **검증 (QA Validation):** 
    작업이 끝난 즉시 `MethodologyAgent`가 해당 결과물이 GSD 룰에 어긋나지 않는지 조사합니다. 실패 시 해당 워크트리는 파기됩니다.
4.  **역병합 및 청소 (Merge & Cleanup):** 
    검사에 합격한 브랜치들만 취합(`CompositionAgent` 개입 유도)하여 메인 작업선으로 `git merge`를 수행합니다. 이후 일회성으로 쓰여진 `worktrees/temp_X` 임시 폴더와 브랜치는 깔끔하게 삭제(Cleanup)됩니다.

> 개발자는 ಈ 에이전트 팀과 워크플로우에 기반하여 코드를 수정하고 로직을 고도화해야 합니다. 상세한 원리 및 규칙은 `docs/GSD.md` 문서를 참고하십시오.
