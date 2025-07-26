# Analysis Agent

![Version](https://img.shields.io/badge/version-1.0.0-blue)
![Python](https://img.shields.io/badge/python-3.13+-green)
![FastAPI](https://img.shields.io/badge/FastAPI-0.111.0-brightgreen)
![React](https://img.shields.io/badge/React-18.2.0-blue)
![Tests](https://img.shields.io/badge/tests-passing-brightgreen)
![Status](https://img.shields.io/badge/status-production--ready-success)

An AI-powered data analysis tool that allows you to upload CSV/Excel files and ask questions about your data using natural language. Built with FastAPI, React, and Google's Gemini AI.

## 🚀 Features

- **File Upload**: Support for CSV, XLSX, and XLS files (up to 50MB)
- **Natural Language Queries**: Ask questions about your data in plain English
- **AI-Powered Analysis**: Uses Gemini 1.5 Flash for intelligent data interpretation
- **Tool-Based Architecture**: Modular tools for different analysis types
- **Session Management**: Multi-session support with data persistence
- **Modern UI**: Clean, responsive interface built with React and Tailwind CSS
- **Comprehensive Testing**: Full integration test suite with 100% pass rate
- **Structured Logging**: JSON-formatted logging with session tracking

## 🏗️ Architecture

```
[User] → [React Frontend] → [FastAPI Backend] → [Orchestrator] → [Analysis Tools] → [Gemini LLM] → [Response]
```

### Components

1. **Frontend** (`frontend/`): React + Vite + Tailwind CSS chat interface
2. **Backend** (`backend/`): FastAPI server with async support and session management
3. **Orchestrator** (`backend/orchestrator.py`): Coordinates tool execution and LLM interactions
4. **Analysis Tools** (`backend/tools/`): 
   - **Data Cleaner**: Standardizes and cleans uploaded data
   - **Metadata Analyzer**: Provides comprehensive data structure analysis
   - **Variance Analyzer**: Compares time periods and calculates statistical variances
   - **Trend Analyzer**: Identifies data trends and patterns over time
5. **LLM Integration** (`backend/llm/`): Flexible provider system supporting Google Gemini
6. **Session Management** (`backend/session.py`): In-memory session storage with conversation history

## 🛠️ Technology Stack

### Backend
- **FastAPI 0.111.0** - Modern Python web framework
- **Pandas 2.3.1** - Data manipulation and analysis
- **Google Generative AI 0.7.1** - Gemini LLM integration
- **Pydantic 2.8.2** - Data validation and settings management
- **Uvicorn 0.30.1** - ASGI server
- **Pytest 8.2.2** - Testing framework with async support

### Frontend
- **React 18.2.0** - UI framework
- **Vite 5.0.0** - Build tool and dev server
- **Tailwind CSS 3.3.5** - Utility-first CSS framework
- **Axios 1.6.2** - HTTP client

## 🚀 Getting Started

### Prerequisites

- **Python 3.13+** (tested with Python 3.13.1)
- **Node.js 16+** 
- **Google Gemini API key** ([Get one here](https://makersuite.google.com/app/apikey))

### Backend Setup

1. **Clone the repository**:
   ```bash
   git clone <repository-url>
   cd Agent_Workflow_Manus
   ```

2. **Create a virtual environment**:
   ```bash
   python -m venv venv
   source venv/bin/activate  # On Windows: venv\Scripts\activate
   ```

3. **Install dependencies**:
   ```bash
   pip install -r requirements.txt
   ```

4. **Set up environment variables**:
   ```bash
   # Create .env file in the root directory
   echo "GEMINI_API_KEY=your_gemini_api_key_here" > .env
   ```

5. **Run the backend server**:
   ```bash
   python -m backend.main
   ```
   The server will start at `http://localhost:8000`

### Frontend Setup

1. **Navigate to frontend directory**:
   ```bash
   cd frontend
   ```

2. **Install dependencies**:
   ```bash
   npm install
   ```

3. **Start the development server**:
   ```bash
   npm run dev
   ```
   The frontend will start at `http://localhost:5173`

## 🧪 Testing

### Running Tests
```bash
# Run all integration tests
pytest backend/tests/test_integration.py -v

# Run with coverage
pytest backend/tests/test_integration.py -v --cov=backend

# Run specific test
pytest backend/tests/test_integration.py::TestIntegrationWorkflow::test_complete_workflow -v
```

### Manual Testing
A comprehensive test script is provided:
```bash
python test_app.py
```

This tests:
- Health check endpoint
- File upload functionality
- Chat/analysis capabilities
- Session management

## 📡 API Endpoints

### Core Endpoints
- `GET /api/health` - Health check
- `POST /api/upload` - File upload with session management
- `POST /api/chat` - Natural language queries and analysis
- `GET /api/session/{session_id}` - Session information
- `GET /docs` - Interactive API documentation (Swagger UI)

### Example Usage

**File Upload:**
```bash
curl -X POST "http://localhost:8000/api/upload" \
  -F "session_id=test123" \
  -F "file=@data.csv"
```

**Chat Query:**
```bash
curl -X POST "http://localhost:8000/api/chat" \
  -H "Content-Type: application/json" \
  -d '{"session_id":"test123","message":"What is the average salary by department?"}'
```

## 🔧 Configuration

### Environment Variables
- `GEMINI_API_KEY` - Your Google Gemini API key (required)
- `LLM_MODEL` - Model name (default: "gemini-1.5-flash-latest")
- `MAX_FILE_SIZE` - Maximum upload size in bytes (default: 52428800 = 50MB)

### Settings
Configuration is managed through `backend/config.py` using Pydantic Settings with environment variable support.

## 🗂️ Project Structure

```
Agent_Workflow_Manus/
├── backend/
│   ├── __init__.py
│   ├── main.py              # FastAPI application entry point
│   ├── config.py            # Configuration management
│   ├── models.py            # Pydantic models
│   ├── orchestrator.py      # Main orchestration logic
│   ├── session.py           # Session management
│   ├── logger.py            # Structured logging setup
│   ├── llm/
│   │   ├── base.py          # LLM base classes
│   │   ├── factory.py       # LLM provider factory
│   │   └── gemini.py        # Google Gemini integration
│   ├── tools/
│   │   ├── __init__.py
│   │   ├── base.py          # Tool base classes
│   │   ├── data_cleaner.py  # Data cleaning tool
│   │   ├── metadata_analyzer.py
│   │   ├── trend_analyzer.py
│   │   └── variance_analyzer.py
│   └── tests/
│       └── test_integration.py  # Comprehensive integration tests
├── frontend/
│   ├── src/
│   │   ├── components/      # React components
│   │   ├── utils/          # Utility functions
│   │   └── ...
│   ├── package.json
│   └── ...
├── requirements.txt         # Python dependencies
├── test_app.py             # Manual testing script
├── test_data.csv           # Sample data for testing
├── pytest.ini             # Pytest configuration
├── README.md
└── CHANGELOG.md
```

## 🤝 Contributing

1. Fork the repository
2. Create a feature branch (`git checkout -b feature/amazing-feature`)
3. Commit your changes (`git commit -m 'Add amazing feature'`)
4. Push to the branch (`git push origin feature/amazing-feature`)
5. Open a Pull Request

### Development Guidelines

- Write tests for new features
- Follow the existing code style
- Update documentation for API changes
- Ensure all tests pass before submitting

## 📝 License

This project is licensed under the MIT License - see the LICENSE file for details.

## 🆘 Troubleshooting

### Common Issues

1. **Import errors when starting the server**:
   - Make sure you're running from the project root: `python -m backend.main`
   - Check that all dependencies are installed: `pip install -r requirements.txt`

2. **Gemini API errors**:
   - Verify your API key is correct and active
   - Check API quota and billing status

3. **File upload issues**:
   - Ensure file size is under 50MB
   - Supported formats: CSV, XLSX, XLS

4. **Port conflicts**:
   - Default backend port is 8000, frontend is 5173
   - Change ports in configuration if needed

### Performance Tips

- For large datasets, consider chunking the data
- Use specific queries for better analysis results
- Monitor memory usage with large files

## 🔮 Roadmap

- [ ] Support for more file formats (JSON, Parquet)
- [ ] Advanced visualization capabilities
- [ ] Export analysis results
- [ ] Real-time collaborative analysis
- [ ] Custom tool development framework
- [ ] Cloud deployment support