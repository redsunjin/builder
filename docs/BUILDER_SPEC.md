# AI Builder Product Specification

## 1. 개요 (Product Overview)
AI Builder는 단일 거대 모델이 전체 코드를 생성하는 방식의 비효율(레이아웃 충돌, 환각, 막대한 토큰 비용)을 해결하기 위한 **'컴포넌트 조립형(Component-driven) UI 목업 생성 플랫폼'** 입니다.
사용자의 단순한 한 줄 프롬프트를 입력받아, 토큰 소모를 극적으로 줄인 "최소 단위 코드 캐싱 기법" 및 하이브리드 LLM 파이프라인을 거쳐 완성된 HTML/Tailwind 레이아웃을 제공하는 B2C/B2B SaaS 프로덕트를 지향합니다.

## 2. 주요 기능 스펙 (Core Features)

### 2.1 대화 최소화 및 정규화 엔드포인트
*   **사용자 입력:** "온라인 쇼핑몰 관리자용 고급 대시보드 페이지 만들어줘. 차트랑 최근 주문 내역이 있었으면 좋겠어." 
*   **처리기:** 내부 프롬프트 분석기(Planning)를 통해 사용자의 말을 '컴포넌트 단위 명세(JSON)'로 파싱.
*   **산출 형태:** 
    ```json
    {
      "required_components": ["admin_sidebar", "top_header", "sales_chart_widget", "recent_orders_table", "footer"],
      "theme": "premium_dark"
    }
    ```

### 2.2 토큰 극강 최적화 라이브러리 연동
*   전체 페이지 생성을 다시 AI에게 맡기지 않고, 기 파싱된 `required_components` 중 이미 시스템 `output/components/` 에 저장된(Cached) 컴포넌트는 DB 조회만으로 텍스트를 즉시 반환.
*   이로 인해 반복 요소를 재생성하는데 소모되는 API 비용과 시간을 약 50% 이상 절감.

### 2.3 커스텀 원자 컴포넌트 동적 생성
*   캐시(Library)에 존재하지 않는 특수 요청이 들어오면, LLM에게 '전체 페이지 레이아웃' 맥락을 주지 않고 오직 '해당 원자 컴포넌트 파츠(Atomic part)' 하나만 생성하라고 제약 조건을 걸어 호출.
*   예: "sales_chart_widget만 꼬이지 않게 독립된 flexbox 형태로 생성해."

### 2.4 안전 조립 로직 (Safe Composition)
*   사용자에게 최종 제공되는 결과물은 개별적으로 완벽히 검증받은 조각들의 조립본.
*   Grid, Flex 기반의 메인 레이아웃 템플릿(CSS Scoping 적용)에 블록을 끼워 넣는 방식으로 렌더링.

## 3. 타겟 사용자 (Target Audience)
*   프로그래밍 지식이 없는 초기 기획자, 아이디어 구상자 (No-Code Experience)
*   와이어프레임을 빠르게 프론트엔드 코드로 변환하고 싶은 디자이너
*   개인 프로젝트의 뼈대 보일러플레이트를 단숨에 쌓길 원하는 1인 개발자

## 4. 백엔드(서버) 스펙 요약
*   **웹 프레임워크:** Python Flask (단기적으로 API 및 Jinja 템플릿 제공) -> FastAPI 또는 Next.js(App Router)로 확장 대기.
*   **저장소:** 초반 `JSON/File System` 기반 -> 중장기적으로 `PostgreSQL` 문서 캐싱 및 유저 세션 관리 도구 연동.
