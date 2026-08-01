import urllib.request
import json
import urllib.error

key = "AQ.Ab8RN6KZTfZhIPAYV0PVXdKJ4eok5v4q_5H6DUUbd65TUNKuMg"
url = f"https://generativelanguage.googleapis.com/v1beta/models/gemini-flash-latest:generateContent?key={key}"

payload = {
    "contents": [{"role": "user", "parts": [{"text": "Hello"}]}],
    "generationConfig": {"temperature": 0.7}
}

try:
    data = json.dumps(payload).encode('utf-8')
    req = urllib.request.Request(url, data=data, headers={'Content-Type': 'application/json'})
    with urllib.request.urlopen(req) as response:
        print("SUCCESS:")
        print(response.read().decode('utf-8'))
except urllib.error.HTTPError as e:
    print(f"ERROR CODE: {e.code}")
    print(e.read().decode('utf-8'))
except Exception as e:
    print(f"OTHER ERROR: {e}")
