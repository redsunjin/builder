# Git Worktree Multi-Agent Framework Roadmap

본 문서는 특정 프로덕트의 기능을 다루는 것이 아닌, **[AI 기반 개발팀(가상 협업 모델) 자체를 어떻게 고도화할 것인가]** 에 대한 엔진 레벨의 발전 로드맵입니다.

---

## Phase 1: Core Lifecycle & Orchestration (현재 완료)
**목표:** 다수 에이전트의 단일 컨텍스트 문제 해결을 위한 병렬/격리 기반 구조 설계

*   [x] **Worktree 기반 물리적 격리:** 하위 폴더(`worktrees/temp_X`) 단위의 병렬 Git Workspace 생성/회수 파이프라인 구현
*   [x] **명시적 라이프사이클 분리:** Planning -> Isolated Generation -> Static QA -> Composition 흐름의 오케스트레이터 추상화
*   [x] **Rule-based 방어막:** Methodology Agent를 도입하여 본선 병합 이전에 파편 조각들을 정규식 기반으로 1차 방어(필터링)하는 시스템 구축

---

## Phase 2: Agent Autonomy & Router (현재 집중 단계)
**목표:** 에이전트 간의 소통을 강화하고, 모델 효율성을 극대화하는 자원 할당 시스템 도입

*   [ ] **다중 모델 라우터 (Multi-LLM Router):** 
    *   작업 난이도를 판별하여, 단순 코딩(Generation)에는 초경량/로컬 모델을 배포하고 구조(Planning/QA) 설계에는 대규모 고지능 모델을 자동 분배하는 허브 인터페이스 구축.
*   [ ] **충돌 회복(Conflict Resolution) 자동화:** 
    *   각 워크트리가 공용 라이브러리/DB 인덱스 등을 동시에 수정할 때 발생하는 Git Merge 충돌 양상을 분석하고, AI가 스스로 충돌을 해결하여 Rebase 하도록 유도.
*   [ ] **스키마 복구 (Self-Correction):** 
    *   에이전트 간 JSON/YAML 통신 구조 파괴시 오케스트레이터가 즉각 파기하는 대신 재시도(Retry) 지침을 프롬프트로 역주입하는 로직 구조화.

---

## Phase 3: Self-Healing & AI-driven QA (신뢰성 도약)
**목표:** 단순한 룰 검사를 넘어, AI가 스스로 코드를 리뷰하고 재작업을 지시하는 메타 인지 시스템

*   [ ] **LLM 기반 동적 코드 리뷰어:** 
    *   Methodology Agent의 역할을 고도화하여 정적 에러뿐만 아니라, 컴포넌트의 논리적 결함(설계 의도 위배 등)을 LLM 코파일럿처럼 리뷰하여 반려(Fail) 리포트를 작성.
*   [ ] **순환 피드백 루프 (Feedback Loop):** 
    *   QA에서 반려된 작업물을 파기하지 않고, 실패 사유(Error Trace)를 컨텍스트로 담아 Generation Agent의 워크트리에 다시 주입(`git commit --amend` 또는 신규 커밋)하여 스스로 코드를 수정하게 만듦 (Self-healing).
*   [ ] **Long-term Context Memory:** 
    *   과거에 여러 번 실패했던 코드 생성 패턴을 벡터 스토어(RAG)에 저장하여, 새로운 스레드(워크트리)가 생성될 때 '과거의 오답과 조언'을 사전 주입.

---

## Phase 4: Containerization & Cloud Scaling (스케일 아웃)
**목표:** 로컬 파일 시스템 제약을 극복하고 이 팀 엔진을 대규모 클라우드에 배포

*   [ ] **스레드 엔진 변경:** 로컬 프로세스(`ThreadPoolExecutor`) 대신 큐잉 시스템(Celery/RabbitMQ)을 통한 분산 비동기 처리 도입.
*   [ ] **Ephemeral 컨테이너 격리:** 물리적인 디스크 용량을 차지하는 Git Worktree 방식을 넘어서, 각 Generation Agent를 일회용 도커 컨테이너(K8s Pods) 또는 Serverless 파이프라인 환경에 올려 완전히 격리된 OS 단위를 제공하는 무한 확장 프레임워크로 이관.
