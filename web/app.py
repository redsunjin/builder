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
    # 디버그 모드로 5000 포트 구동
    app.run(host='0.0.0.0', port=5000, debug=True)
