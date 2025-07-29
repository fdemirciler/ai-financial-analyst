import requests

url = "http://localhost:8001/api/upload"
files = {
    "file": (
        "test_data.csv",
        open(r"c:\Users\fdemi\Documents\Code\Agent_Workflow_Qwen\test_data.csv", "rb"),
    )
}
data = {"session_id": "test_debug_session"}

try:
    response = requests.post(url, files=files, data=data)
    print(f"Status Code: {response.status_code}")
    print(f"Response: {response.text}")
except Exception as e:
    print(f"Error: {e}")
