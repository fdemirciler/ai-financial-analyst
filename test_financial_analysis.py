import requests
import json

# Test financial analysis queries that are appropriate for balance sheet data
session_id = "financial_test"

print("🏦 Testing Financial Analysis with Balance Sheet Data")
print("=" * 60)

# Upload file
print("📁 Uploading balance sheet data...")
files = {"file": ("test_data.csv", open("test_data.csv", "rb"))}
data = {"session_id": session_id}
response = requests.post("http://localhost:8000/api/upload", files=files, data=data)
print(f"Upload Status: {response.status_code}")

# Test 1: Trend analysis of Total Assets
print("\n📈 Test 1: Asset Growth Analysis")
chat_data = {
    "session_id": session_id,
    "message": "Analyze the trend in Total Assets from 2022 to 2025. What's the growth pattern?",
}
response = requests.post("http://localhost:8000/api/chat", json=chat_data)
result = response.json()
print(f"Status: {response.status_code}")
print(f"Analysis: {result['response'][:200]}...")
print(f"Tool Used: {result['tool_used']}")

# Test 2: Variance analysis
print("\n📊 Test 2: Year-over-Year Variance")
chat_data = {
    "session_id": session_id,
    "message": "Compare 2024 vs 2025 performance. What are the key changes in the balance sheet?",
}
response = requests.post("http://localhost:8000/api/chat", json=chat_data)
result = response.json()
print(f"Status: {response.status_code}")
print(f"Analysis: {result['response'][:200]}...")
print(f"Tool Used: {result['tool_used']}")

# Test 3: Metadata overview
print("\n🔍 Test 3: Data Overview")
chat_data = {
    "session_id": session_id,
    "message": "Give me an overview of this financial dataset. What columns and data do we have?",
}
response = requests.post("http://localhost:8000/api/chat", json=chat_data)
result = response.json()
print(f"Status: {response.status_code}")
print(f"Analysis: {result['response'][:200]}...")
print(f"Tool Used: {result['tool_used']}")

print("\n✅ Financial Analysis Testing Complete!")
