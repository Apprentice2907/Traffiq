import requests
url = "http://localhost:8000/api/feedback/analyze"
try:
    print("Triggering feedback analysis...")
    response = requests.post(url)
    print(response.json())
except Exception as e:
    print(f"Error: {e}")
