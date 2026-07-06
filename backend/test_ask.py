import requests

url = "http://localhost:8000/api/ask"

questions = [
    "Which zone is worst at night?",
    "Why is zone Z12 high risk?",
    "What should officers do at 2PM?",
    "Which day has the most violations?"
]

for q in questions:
    print(f"Question: {q}")
    try:
        response = requests.post(url, json={"question": q})
        print(response.json())
    except Exception as e:
        print(f"Error: {e}")
    print("-" * 40)
