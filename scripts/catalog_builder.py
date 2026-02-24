import os
import sys
import time

# Add root directory to python path
base_dir = os.path.abspath(os.path.join(os.path.dirname(__file__), '..'))
if base_dir not in sys.path:
    sys.path.append(base_dir)

from worktrees.generation_agent.agent import GenerationAgent

def build_catalog():
    print("==========================================")
    print("🛠️  GSD Phase Gamma: Component Catalog Builder")
    print("==========================================")
    print("목적: GSD 원칙(격리된 원자적 실행)에 따라 신규 컴포넌트들을 라이브러리에 사전 적재합니다.")
    print("방식: GenerationAgent를 독립적으로 1회씩 호출하여 안전하게 생성/저장합니다.")
    
    components_to_build = [
        "hero_section",
        "feature_list",
        "pricing_table",
        "testimonial_card",
        "footer_simple",
        "nav_bar",
        "login_form",
        "alert_banner",
        "faq_accordion",
        "modal_dialog"
    ]

    # 독립된 에이전트 인스턴스 (실제로는 호출 시마다 생성하는 것이 GSD에 더 부합함)
    agent = GenerationAgent()
    
    success_count = 0
    
    for idx, comp_name in enumerate(components_to_build, 1):
        print(f"\n[{idx}/{len(components_to_build)}] '{comp_name}' 컴포넌트 생성 요청 중...")
        try:
            # GSD 원칙: 컨텍스트 간섭 없이 한 번에 하나의 컴포넌트만 생성
            # (load_component_metadata 로직 내부에 라이브러리 검사 및 LLM 호출 로직이 포함됨)
            result = agent.load_component_metadata(comp_name)
            if result and result.get("name") == comp_name:
                success_count += 1
            time.sleep(1)  # API Rate limit 방지 보수적 슬립
        except Exception as e:
            print(f"❌ '{comp_name}' 생성 중 오류 발생: {e}")

    print("\n==========================================")
    print(f"✅ 카탈로그 구출 완료: {success_count}/{len(components_to_build)} 성공")
    print(f"저장 위치: {agent.library_path}")
    print("==========================================")

if __name__ == "__main__":
    build_catalog()
