import requests
import json

# Test 1: Health check
print("Testing health endpoint...")
response = requests.get("http://localhost:8001/api/health")
print(f"Health check: {response.status_code} - {response.json()}")

# Test 2: File upload
print("\nTesting file upload...")
files = {"file": ("test_data.csv", open("test_data.csv", "rb"))}
data = {"session_id": "test123"}
response = requests.post("http://localhost:8001/api/upload", files=files, data=data)
print(f"Upload: {response.status_code} - {response.json()}")

# Test 3: Chat message
print("\nTesting chat functionality...")
chat_data = {
    "session_id": "test123",
    "message": "Can you analyze the salary data and show me the average salary by department?",
}
response = requests.post("http://localhost:8001/api/chat", json=chat_data)
print(f"Chat: {response.status_code} - {response.json()}")

# Test 4: Session info
print("\nTesting session info...")
response = requests.get("http://localhost:8001/api/session/test123")
print(f"Session info: {response.status_code} - {response.json()}")
