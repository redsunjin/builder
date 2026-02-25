import sys
import os

# Add root directory to sys.path
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from web.app import app

if __name__ == '__main__':
    print("[Server] Starting AI Builder Web Interface...")
    app.run(host='0.0.0.0', port=5000, debug=True)
