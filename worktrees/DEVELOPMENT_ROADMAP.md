# AI Builder Worktree Framework Development Roadmap

이 문서는 AI Builder 프로젝트의 핵심 코어인 **[Git Worktree 기반 멀티-에이전트 개발 방법론]** 을 지속적으로 고도화하기 위한 개발 로드맵입니다.

---

## Phase 1: 기반 아키텍처 및 GSD 파이프라인 (현재 완료 단계)
**목표:** 다중 에이전트의 개념 설계 및 스레드 격리 기반 확립

*   [x] **프로젝트 기본 폴더 구조화:** `worktrees/`, `core/`, `output/` 레이아웃 정리
*   [x] **Git Manager 개발:** Python 스크립트 기반 `add_worktree`, `commit`, `merge`, `remove` 동작 추상화 (`scripts/git_manager.py`)
*   [x] **병렬 비동기 오케스트레이터:** `ThreadPoolExecutor`를 통한 다수 워크트리의 동시 다발적 생성 및 통합 데모 (`core/orchestrator.py`)
*   [x] **Methodology/QA Agent 도입:** 정적 검사(HTML 태그 유무 검출 등)를 통해 GSD 원칙을 방어하는 QA 게이트웨이 추가

---

## Phase 2: 안정성 고도화 및 LLM 결합 (현재 집중 단계)
**목표:** 임시 파이프라인의 에러 핸들링을 튼튼히 하고, 실제 LLM을 연결하여 "진짜 AI 에이전트" 화

*   [ ] **LLM Router 연동 (예정):** 
    *   `src/utils/llm_router.py` 고도화
    *   단순 컴포넌트는 속도/비용이 저렴한 로컬 모델(Ollama) 배정.
    *   복잡한 로직이나 Layout 조율은 고지능 모델(OpenAI/Gemini) 배정.
*   [ ] **메타데이터 파서 강건성 확보:** 
    *   `Customer Agent`가 반환하는 JSON의 스키마 에러 복구(Self-Correct) 메커니즘 구축.
*   [ ] **충돌 처리(Merge Conflict) 메커니즘 구체화:** 
    *   여러 워크트리가 동시에 같은 위치(예: 라이브러리 인덱스)를 수정할 때 발생하는 Git Conflict 자동 롤백 및 재시도 기능 구현.
*   [ ] **텔레메트리(Telemetry) 대시보드 연동:** 
    *   비용 절감 지표(Cache Hit 비율 등) 데이터를 영구 저장(DB 혹은 SQLite 연동)하고 프론트엔드와 연결.

---

## Phase 3: QA 고도화 및 피드백 루프 (확장 단계)
**목표:** 에이전트들이 사람의 개입 없이 스스로 코드를 리뷰하고 결함을 수정하는 자가 치유(Self-Healing) 파이프라인 구축

*   [ ] **LLM 기반 동적 QA 리뷰어:** 
    *   현재의 정규식 기반 정적 검사를 넘어, `Methodology Agent` 가 "사용자의 본래 의도와 디자인에 맞는가?" 를 LLM으로 교차 검증하는 기능 추가.
*   [ ] **리트라이 및 피드백 루프 파이프라인:** 
    *   QA 실패 시 해당 워크트리를 즉각 폐기하는 현재 구조에서, **"실패 로그를 컨텍스트로 첨부하여 Generation Agent에게 재성성 요처(Retry)"** 하도록 오케스트레이터 강화. (최대 3회 제한 등)
*   [ ] **컨텍스트 자동 압축:** 
    *   피드백이 너무 순환되어 토큰 한도를 넘지 않도록, 실패 로그를 벡터 스코어링하여 핵심 에러만 압축 전달하는 시스템 개발.

---

## Phase 4: 배포 파이프라인 (Deploy & CI/CD)
**목표:** 로컬 환경을 벗어난 서비스화

*   [ ] **비동기 큐잉 시스템 (Celery / Redis) 도입:**
    *   웹(Flask) 단에서 사용자가 다수 몰렸을 때 Git Worktree 병렬 생성이 서버 스레드를 독점하지 못하게 대기열 시스템 도입.
*   [ ] **Git Worktree 컨테이너화:** 
    *   물리적 폴더(워크트리) 생성이 아닌, Docker 컨테이너(K8s Pod 단위)에서 각 에이전트를 휘발성(Ephemeral)으로 실행하도록 최종 발전.
