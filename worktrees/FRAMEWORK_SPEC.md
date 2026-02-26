# AI Builder Worktree Framework Specification

## 1. 프레임워크 개요 (Framework Overview)
이 스펙 문서는 AI Builder 프로젝트의 프로덕트(UI 컴포넌트 조립)를 넘어서, **AI 기반 에이전트들이 Git Worktree를 활용하여 어떻게 안전하고 격리된 환경에서 협업(개발)해야 하는지**에 대한 기술적 정의서입니다. 
GSD(Get Stuff Done) 철학에 따라, 단일 AI 모델의 맥락 오염(Context Rot)을 막고 다수 에이전트의 책임을 분리하는 것이 핵심입니다.

## 2. 에이전트 구성 및 역할 (Agent Roles)

### 2.1 Customer Agent (분석가/파서)
*   **실행 위치:** 메인 브랜치 (`main`)
*   **Input:** 사용자의 자연어 요청 (예: "대시보드 페이지와 로그인 폼 만들어줘")
*   **Output:** 필수 컴포넌트 목록과 세션 ID가 포함된 정규화된 JSON 포맷 (`interfaces/agent_interfaces.json` 참고)
*   **제약사항:** 코드(HTML/CSS) 생성에 관여하지 않으며, 오직 "어떤 부품이 필요한가"만 결정합니다.

### 2.2 Methodology / QA Agent (아키텍트/테스터)
*   **실행 위치:** 파이프라인 전반 감시 및 격리된 워크트리 검수
*   **Input:** `Generation Agent` 가 생성한 컴포넌트 데이터 조각
*   **Output:** `Pass` / `Fail` 상태 리포트 및 반려(Reject)
*   **검증 규칙 (Rule-based QA):**
    *   **GSD Rule 1:** 산출물은 `<html>`, `<body>`, `<head>` 등의 전체 문서 구조를 포함해서는 안 됨 (컴포넌트 단위 강제).
    *   **GSD Rule 2:** 생성된 코드가 사전 정의된 JSON 구조(메타데이터, html 텍스트 등)를 만족해야 함.
*   **제약사항:** 직접 코드를 수정하지 않으며, 실패 시 해당 임시 브랜치 및 워크트리의 통째 삭제(Drop)를 오케스트레이터에 지시합니다.

### 2.3 Generation Agent (분산 AI 코더)
*   **실행 위치:** `worktrees/temp_<component_name>` (격리된 임시 폴더 및 브랜치)
*   **Input:** Customer Agent가 도출한 '단일' 컴포넌트 이름 (목표 단위)
*   **Output:** 컴포넌트 구조를 담은 `.json` 파일
*   **비용 절감 전략:** 생성 전 `output/components/` (혹은 라이브러리 캐시)를 조회하여 기존 파일이 존재하면 LLM을 호출하지 않고 캐시를 반환합니다 (Hit).
*   **제약사항:** 한 번에 오직 하나의 컴포넌트에 대해서만 코드를 생성해야 합니다 (Atomic Execution). 

### 2.4 Composition Agent (조립/퍼블리셔)
*   **실행 위치:** 메인 브랜치 병합 단계
*   **Input:** Methodology QA를 통과한 다수의 컴포넌트 브랜치들 및 메타데이터
*   **Output:** 병합 충돌 해결 및 최종 조립된 `output/builder_output.html`
*   **제약사항:** 템플릿의 전체적인 레이아웃(Grid, Flex 등)에만 개입하며 개별 컴포넌트의 내부 디자인 로직은 건드리지 않습니다.

## 3. 오케스트레이션 및 라이프사이클 (Orchestration Pipeline)
`core/orchestrator.py` 가 `git_manager.py`를 활용하여 다음 라이프사이클을 자동 통제해야 합니다.

1.  **Job Parsing:** `Customer Agent` 가 타겟 컴포넌트 리스트 도출.
2.  **Thread Allocation (분산 할당):** `ThreadPoolExecutor` 를 통해 타겟 별로 독립된 워크트리(`feat/X_gen`) 생성.
3.  **Atomic Generation:** 각 스레드에서 `Generation Agent`가 LLM 호출 및 파일 쓰기.
4.  **Local Commit:** 워크트리 내부에서 `git commit` 수행.
5.  **QA Gate (품질 검문):** `Methodology Agent` 가 결과물을 정적 분석.
6.  **Branch Cleanup (성공/실패 분기):**
    *   **성공 (Pass):** 임시 브랜치를 `main` 에 `merge` (충돌 무시-허용 옵션) 후 임시 워크트리 폴더 삭제.
    *   **실패 (Fail):** 해당 임시 브랜치 및 워크트리 즉각 폐기, `Telemetry` 대시보드에 에러 리포트.
7.  **Final Composition:** 살아남아 병합된 조각들을 모아 `Composition Agent` 가 하나의 템플릿 완성.

## 4. 확장성 스펙 (Future Portability)
*   현재 Python 로컬 `subprocess` 기반의 Git 호출을 장기적으로 Github Actions 환경 혹은 별도 컨테이너 클러스터(Kubernetes) 기반의 MSA 구조로 분리할 수 있도록 설계합니다.
*   다양한 LLM (OpenAI, Gemini, Ollama) 을 교체할 수 있도록 `Generation Agent` 의 호출부는 반드시 `llm_router.py` 인터페이스만을 통과해야 합니다.
