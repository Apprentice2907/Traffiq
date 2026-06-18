import requests
import time

print("Waiting for server to start...")
for i in range(15):
    try:
        requests.get("http://localhost:8000/api/trend")
        break
    except:
        time.sleep(2)

try:
    print("\n--- /api/report ---")
    print(requests.get("http://localhost:8000/api/report").text[:500] + "...\n[Report Truncated for display]")

    print("\n--- /api/query ---")
    res = requests.post("http://localhost:8000/api/query", json={"question": "which zone is worst at night?"})
    print(res.text)
except Exception as e:
    print(f"Error testing API: {e}")
