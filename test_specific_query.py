import requests

# Test with a very specific financial query
session_id = "detailed_test"

print("💰 Testing Detailed Financial Query")
print("=" * 40)

# Upload file
files = {"file": ("test_data.csv", open("test_data.csv", "rb"))}
data = {"session_id": session_id}
requests.post("http://localhost:8000/api/upload", files=files, data=data)

# Ask for specific cash flow analysis
chat_data = {
    "session_id": session_id,
    "message": "What is the exact value of Cash & Equivalents in 2025? Show me the raw data.",
}
response = requests.post("http://localhost:8000/api/chat", json=chat_data)
result = response.json()

print(f"Status: {response.status_code}")
print(f"Full Response: {result['response']}")
print(f"Tool Used: {result['tool_used']}")
print(
    f"Data Available: {len(result.get('data', [])) if result.get('data') else 0} records"
)
