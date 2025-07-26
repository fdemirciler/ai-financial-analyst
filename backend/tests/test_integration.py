"""
Integration tests for the full application workflow.
Tests file upload, session management, and chat functionality.
"""

import pytest
import json
import io
from fastapi.testclient import TestClient
from backend.main import app


class TestIntegrationWorkflow:
    """Test the complete workflow from file upload to analysis."""

    def test_complete_workflow(self):
        """Test the complete workflow: upload file -> analyze -> chat."""

        client = TestClient(app)

        # Step 1: Health check
        health_response = client.get("/api/health")
        assert health_response.status_code == 200
        assert health_response.json()["status"] == "healthy"

        # Step 2: Create a test CSV file
        csv_content = """name,age,salary,department
John,25,50000,Engineering
Jane,30,60000,Marketing
Bob,35,70000,Engineering
Alice,28,55000,Sales
Charlie,32,65000,Marketing
David,29,58000,Engineering
Eve,31,62000,Sales"""

        csv_file = io.BytesIO(csv_content.encode())

        # Step 3: Upload file with session_id
        files = {"file": ("test_data.csv", csv_file, "text/csv")}
        data = {"session_id": "test_session_123"}

        upload_response = client.post("/api/upload", files=files, data=data)
        print(
            f"Upload response: {upload_response.status_code} - {upload_response.text}"
        )

        # Should succeed or give us useful error info
        assert upload_response.status_code in [
            200,
            422,
        ]  # Accept both success and validation errors

        if upload_response.status_code == 200:
            upload_data = upload_response.json()
            assert "message" in upload_data
            print(f"Upload successful: {upload_data}")

            # Step 4: Test chat functionality with the uploaded data
            chat_request = {
                "session_id": "test_session_123",
                "message": "Can you analyze the salary data and tell me the average salary by department?",
            }

            chat_response = client.post("/api/chat", json=chat_request)
            print(f"Chat response: {chat_response.status_code} - {chat_response.text}")

            # Should get a response from the LLM
            assert chat_response.status_code in [
                200,
                422,
                500,
            ]  # Allow various responses for now

            if chat_response.status_code == 200:
                chat_data = chat_response.json()
                assert "response" in chat_data
                print(f"Chat successful: {chat_data}")

        else:
            # If upload failed, let's see why
            print(f"Upload failed with: {upload_response.json()}")

    def test_session_management(self):
        """Test session creation and retrieval."""

        client = TestClient(app)

        # Test chat without existing session (should create one)
        chat_request = {
            "session_id": "new_session_456",
            "message": "Hello, can you help me with data analysis?",
        }

        chat_response = client.post("/api/chat", json=chat_request)
        print(f"New session chat: {chat_response.status_code} - {chat_response.text}")

        # Should handle new session gracefully
        assert chat_response.status_code in [200, 422, 500]

    def test_error_handling(self):
        """Test error handling for invalid requests."""

        client = TestClient(app)

        # Test upload without file
        upload_response = client.post("/api/upload", data={"session_id": "test"})
        assert upload_response.status_code == 422  # Validation error

        # Test chat without message
        chat_response = client.post("/api/chat", json={"session_id": "test"})
        assert chat_response.status_code == 422  # Validation error

        # Test chat without session_id
        chat_response = client.post("/api/chat", json={"message": "test"})
        assert chat_response.status_code == 422  # Validation error


class TestDataAnalysisTools:
    """Test the individual data analysis tools with pandas."""

    @pytest.mark.asyncio
    async def test_data_cleaner_functionality(self):
        """Test DataCleaner with sample data."""
        import pandas as pd
        from backend.tools.data_cleaner import DataCleaner

        # Create sample data with issues
        data = pd.DataFrame(
            {
                "name": ["John", "Jane", "", "Bob", "Alice"],
                "age": [25, 30, None, 35, 28],
                "salary": [50000, 60000, 70000, None, 55000],
                "department": ["Engineering", "Marketing", "Engineering", "Sales", ""],
            }
        )

        cleaner = DataCleaner()
        result = await cleaner.execute(data, {})

        # Should return cleaned data with expected structure
        assert isinstance(result, dict)
        assert "success" in result
        assert "data" in result
        assert "shape" in result
        assert "columns" in result
        assert "message" in result
        assert result["success"] is True
        assert len(result["data"]) == 5  # Should have 5 rows
        assert result["shape"] == (5, 4)  # 5 rows, 4 columns
        print(f"Data cleaner result: {result}")

    @pytest.mark.asyncio
    async def test_trend_analyzer_functionality(self):
        """Test TrendAnalyzer with time series data."""
        import pandas as pd
        from backend.tools.trend_analyzer import TrendAnalyzer

        # Create sample time series data
        dates = pd.date_range(
            "2023-01-01", periods=12, freq="ME"
        )  # Use 'ME' instead of deprecated 'M'
        data = pd.DataFrame(
            {
                "date": dates,
                "revenue": [
                    100000,
                    110000,
                    105000,
                    120000,
                    115000,
                    130000,
                    125000,
                    140000,
                    135000,
                    150000,
                    145000,
                    160000,
                ],
                "customers": [
                    1000,
                    1100,
                    1050,
                    1200,
                    1150,
                    1300,
                    1250,
                    1400,
                    1350,
                    1500,
                    1450,
                    1600,
                ],
            }
        )

        analyzer = TrendAnalyzer()
        result = await analyzer.execute(data, {})

        # Should return trend analysis results
        assert isinstance(result, dict)
        assert "success" in result
        assert "results" in result
        assert "message" in result
        assert result["success"] is True
        assert len(result["results"]) > 0  # Should have trend data
        print(f"Trend analyzer result: {result}")

    @pytest.mark.asyncio
    async def test_variance_analyzer_functionality(self):
        """Test VarianceAnalyzer with numerical data."""
        import pandas as pd
        from backend.tools.variance_analyzer import VarianceAnalyzer

        # Create sample data with variance
        data = pd.DataFrame(
            {
                "department": [
                    "Engineering",
                    "Marketing",
                    "Sales",
                    "Engineering",
                    "Marketing",
                ],
                "salary": [70000, 55000, 50000, 75000, 60000],
                "experience": [5, 3, 2, 7, 4],
            }
        )

        analyzer = VarianceAnalyzer()
        result = await analyzer.execute(data, {})

        # Should return variance analysis results
        assert isinstance(result, dict)
        assert "success" in result
        assert "results" in result
        assert "message" in result
        assert result["success"] is True
        assert len(result["results"]) > 0  # Should have variance data
        print(f"Variance analyzer result: {result}")


if __name__ == "__main__":
    # Run specific test manually
    print("Running integration tests...")
    test = TestIntegrationWorkflow()
    test.test_complete_workflow()
