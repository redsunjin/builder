import os
import sys
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from flask import Flask, render_template, request, jsonify
from core.orchestrator import Orchestrator

app = Flask(__name__)

# 초기화 (GSD 생애주기 설정을 로드하는 오케스트레이터 인스턴스)
try:
    orchestrator = Orchestrator()
    print("[Flask] Orchestrator initialized successfully.")
except Exception as e:
    print(f"[Flask] Error initializing Orchestrator: {e}")
    orchestrator = None

@app.route('/')
def index():
    """웹 브라우저 접근 시 UI 표시 (Phase Live)"""
    return render_template('index.html')

@app.route('/api/generate', methods=['POST'])
def generate_ui():
    """프론트엔드로부터 프롬프트를 받아 UI 생성을 요청하는 엔드포인트"""
    if not orchestrator:
        return jsonify({"error": "Orchestrator not initialized. Check server logs."}), 500
        
    data = request.json
    user_intent = data.get('intent', '').strip()
    
    if not user_intent:
        return jsonify({"error": "intent is required."}), 400
        
    session_id = f"web_session_{os.urandom(4).hex()}"
    
    try:
        # Orchestrator 호출 (API 호환 버전)
        result = orchestrator.run_pipeline(session_id, user_intent)
        
        if result is None:
            return jsonify({"error": "Generation blocked or failed (e.g. exceeded component limits)."}), 400
            
        # result 딕셔너리에 담긴 html 코드와 metrics 반환
        return jsonify(result), 200
        
    except Exception as e:
        print(f"[Flask] Error during generation: {e}")
        return jsonify({"error": str(e)}), 500

if __name__ == '__main__':
    # 워크트리가 생성/제거될 때 파일 시스템 변경이 감지되어 서버가 재시작되는 현상(watchdog)을 막기 위해 
    # use_reloader=False 옵션을 추가합니다. (debug=False로 완전 차단)
    app.run(host='0.0.0.0', port=5000, debug=False, use_reloader=False)
