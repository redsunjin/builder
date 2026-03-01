# AI Builder - Local LLM Handoff Guide

## 개요
이 문서는 **AI Builder (Alpha 기반, Beta 준비 단계)** 개발을 로컬 LLM(Ollama 등)이 설치된 장비로 이관하여 후속 테스트 및 프롬프트 엔지니어링을 진행하기 위한 핸즈오프(Handoff) 문서입니다.

현재까지의 진행 상황은 다중 LLM 라우터(`src/utils/llm_router.py`)와 웹 UI(`web/app.py` 및 `index.html`) 연동이 100% 완료된 상태입니다. API 키가 없는 경우에도 안전하게 Mock 데이터로 파이프라인이 붕괴되지 않고 정상 구동되도록 검증을 마쳤습니다.
현재 생애주기 기준 페이즈는 `config/lifecycle_config.json`의 `current_phase=Alpha`입니다.

## 현재까지 구현된 기능 (v0.2 Alpha+)
1.  **Git Worktree + 멀티 에이전트 오케스트레이션**: 병렬로 컴포넌트(브랜치) 생성, QA 검증, 최종 마스터 병합 파이프라인 완성.
2.  **Multi-LLM 라우팅**: OpenAI(gpt-4o), Google(Gemini 1.5), Ollama(로컬) 중 설정에 따라 유연하게 모델 객체를 반환.
3.  **Flask Web UI (Live 준비 단계)**: 채팅 형태로 프롬프트를 입력받고 반환된 HTML을 실시간 렌더링. 컴포넌트 캐시 히트 등 텔레메트리(Telemetry) 지표 출력 완비.
4.  **신뢰성 강화**: 인터럽트/오류 상황의 워크트리 정리, stale recovery, 저널링, 스모크 테스트 스크립트 추가.

## 로컬 장비에서의 세팅 및 실행 방법

### 1. 환경 변수 세팅 (`.env` 파일 구성)
프로젝트 최상단에 있는 `.env.example` 파일을 복사하여 `.env` 파일을 생성하십시오.
로컬에 Ollama가 설치되어 있다면 API 키 없이도 동작하지만, 향후 클라우드 모델을 병용하려면 키를 입력해 둡니다.

```bash
cp .env.example .env
```

### 2. 패키지 설치
LLM 라우터 구동에 필요한 LangChain 관련 패키지가 `requirements.txt`에 명시되어 있지 않다면 수동으로 설치하거나, 이미 설치된 환경 정보를 동기화하십시오. (현재 장비에는 `langchain`, `langchain-community`, `langchain-openai`, `langchain-google-genai` 등이 설치되어 있습니다.)

### 3. 로컬 LLM (Ollama) 준비
현재 에이전트 LLM은 하드코딩이 아닌 환경변수 우선(`AI_PROVIDER`, `AI_MODEL`)으로 동작하며, 기본값은 `provider="ollama"`, `model="llama3"`입니다.
오프라인 로컬 환경에서 테스트하려면 다음 단계를 진행하십시오:

1.  Ollama 설치 및 백그라운드 구동 (`http://localhost:11434`)
2.  적절한 모델 Pull 
    ```bash
    ollama pull llama3
    ```

### 4. 서버 구동
디버그 워치독(watchdog)에 의한 재시작 버그를 해결하기 위해 `run_server.py`는 `debug=False`로 세팅되어 있습니다. 터미널에서 다음 명령어를 실행하십시오.

```bash
python run_server.py
```
브라우저에서 `http://127.0.0.1:5000` 에 접속하여 테스트를 시작합니다.

## Next Steps: 이관 장비에서 즉시 수행할 작업

1.  **로컬 연동 테스트 (Real Test):**
    웹 UI에 "헤더와 버튼, 카드 UI 하나 만들어줘" 라고 입력했을 때, Ollama(또는 세팅한 LLM)가 실제 코드를 반환하고 화면 우측 Preview에 잘 그려지는지 확인.
2.  **프롬프트 엔지니어링 (Prompt Tuning):**
    실제 LLM이 투입되면 마크다운 규칙(```html 등)을 무시하거나 불필요한 텍스트를 같이 반환하여 조립이 깨질 수 있습니다.
    *   `worktrees/customer_agent/agent.py` 의 `PromptTemplate` 수정: "JSON만 반환하라"는 지시어 강화.
    *   `worktrees/generation_agent/agent.py` 수정: Tailwind CSS 코드 덩어리만 반환하도록 지시어 강화.
3.  **UI/UX 개선:** Dashboard CSS 구조 디벨롭 및 Telemetry 레이아웃 고도화.

## 안전 실행 프로토콜 (운영 권장)

`run_pipeline()`를 호출하는 스크립트는 Git 워크트리/브랜치/merge를 동반할 수 있으므로, 아래 순서로 실행하는 것을 권장합니다.

1.  **안전 회귀검증(merge 금지) 먼저 실행**
    ```bash
    source .venv/bin/activate
    python scripts/safety_no_merge_regression.py
    ```
    - 이 테스트는 `ORCHESTRATOR_DISABLE_MERGE=1`을 강제하고, 실행 전/후 `HEAD`가 동일한지 검사합니다.

2.  **신뢰성 스모크는 기본 안전 모드로 실행**
    ```bash
    python scripts/smoke_orchestrator_reliability.py
    ```
    - 기본값은 `ORCHESTRATOR_DISABLE_MERGE=1`이며, temp worktree 정리/저널 종료 상태를 검증합니다.

3.  **merge 허용 실행은 명시적으로만 수행**
    ```bash
    python scripts/smoke_orchestrator_reliability.py --allow-merge
    ```
    - `--allow-merge`는 실제 `main` 변경 가능성이 있으므로, 로컬 실험 브랜치 또는 격리된 저장소에서만 사용하십시오.
