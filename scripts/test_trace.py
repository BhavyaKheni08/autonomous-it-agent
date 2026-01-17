import requests
import sys

def test_trace():
    print("Testing trace creation...")
    url = "http://localhost:8000/api/v1/tickets"
    payload = {
        "user_email": "trace_test@example.com",
        "issue_description": "Tracing test issue description."
    }
    
    try:
        response = requests.post(url, json=payload)
        if response.status_code == 200:
            print("Request successful! Check LangSmith dashboard.")
            print(f"Response: {response.json()}")
        else:
            print(f"Request failed: {response.status_code} - {response.text}")
    except Exception as e:
        print(f"Connection error: {e}")
        print("Ensure the backend container is running.")

if __name__ == "__main__":
    test_trace()
