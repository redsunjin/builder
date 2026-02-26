import requests
import json

url = "http://127.0.0.1:5000/api/generate"
payload = {"intent": "a button and a text input"}
headers = {"Content-Type": "application/json"}

print("Sending request to:", url)
try:
    response = requests.post(url, json=payload)
    print("Status Code:", response.status_code)
    try:
        print("Response JSON:\n", json.dumps(response.json(), indent=2, ensure_ascii=False))
    except Exception:
        print("Raw Response:", response.text)
except Exception as e:
    print("Error:", e)
