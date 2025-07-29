# Analysis Agent - Enhanced Edition

![Version](https://img.shields.io/badge/version-2.0.0-blue)
![Python](https://img.shields.io/badge/python-3.13+-green)
![FastAPI](https://img.shields.io/badge/FastAPI-0.111.0-brightgreen)
![React](https://img.shields.io/badge/React-18.2.0-blue)
![Tests](https://img.shields.io/badge/tests-passing-brightgreen)
![Status](https://img.shields.io/badge/status-production--ready-success)
![Enhanced](https://img.shields.io/badge/Enhanced_Pipeline-Active-orange)

An AI-powered data analysis tool with **enhanced data processing pipeline** that allows you to upload CSV/Excel files and ask questions about your data using natural language. Built with FastAPI, React, and Google's Gemini AI, featuring advanced type inference, layout detection, and comprehensive data quality assessment.

## 🚀 Enhanced Features

### **Advanced Data Processing Pipeline**
- **🧠 Smart Type Inference**: Automatically detects currency, percentages, dates, periods, IDs, and text columns with confidence scoring
- **📊 Layout Detection**: Recognizes wide vs. long format data and normalizes automatically
- **🧹 Intelligent Data Cleaning**: Type-aware cleaning strategies with configurable options
- **📈 Comprehensive Data Profiling**: Statistical analysis, correlation detection, and quality assessment
- **📋 Complete Audit Trail**: Full logging of all data transformations with timestamps
- **🔄 Multi-Sheet Support**: Excel files with multiple sheets processed individually
- **⚡ Chunked Processing**: Efficient handling of large datasets with memory management
- **🛡️ Robust Error Recovery**: Multiple fallback levels for reliable processing

### **Core Features**
- **File Upload**: Support for CSV, XLSX, and XLS files (up to 50MB) with enhanced processing
- **Natural Language Queries**: Ask questions about your data in plain English
- **AI-Powered Analysis**: Uses Gemini 2.5 Flash for intelligent data interpretation
- **Enhanced Tool Architecture**: Advanced modular tools with backward compatibility
- **Session Management**: Multi-session support with enhanced pipeline results storage
- **Modern UI**: Clean, responsive interface built with React and Tailwind CSS
- **Data Quality Scoring**: Automatic assessment of data quality (0-100 scale)
- **Structured Logging**: JSON-formatted logging with comprehensive audit trails

## 🏗️ Enhanced Architecture

```
[User] → [React Frontend] → [FastAPI Backend] → [Enhanced Orchestrator] → [Pipeline Processor] → [Enhanced Tools] → [Gemini LLM] → [Response]
                                                                      ↓
                                                           [Type Inference] → [Layout Detection] → [Smart Cleaning] → [Quality Assessment]
```

### Enhanced Components

1. **Enhanced Pipeline** (`pipeline/`): Advanced data processing engine
   - **Pipeline Orchestrator**: Main processing coordinator
   - **Type Inferencer**: Smart semantic type detection
   - **Layout Detector**: Wide/long format recognition and normalization
   - **Data Cleaner**: Type-aware cleaning with configurable strategies
   - **Data Profiler**: Comprehensive statistical analysis and quality metrics
   - **Audit Logger**: Complete transformation tracking

2. **Enhanced Data Processor** (`backend/services/`): Integration layer
   - **Memory Processing**: Efficient in-memory data handling
   - **Chunked Processing**: Large file support with memory management
   - **Error Recovery**: Multi-level fallback processing
   - **Quality Assessment**: Automatic data quality scoring and reporting

3. **Enhanced Tools** (`backend/tools/enhanced_tools.py`): Advanced analysis tools
   - **Enhanced Data Cleaner**: Type-aware cleaning with period detection
   - **Enhanced Data Profiler**: Statistical analysis with quality metrics
   - **Enhanced Preprocessor**: Smart type inference with confidence scoring

4. **Enhanced Session Management**: Pipeline results storage and multi-sheet support

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

## 🚀 Enhanced Pipeline Capabilities

### 🧠 Smart Type Inference
The enhanced pipeline includes advanced type detection that goes beyond basic data types:

- **Semantic Types**: Currency, percentage, date, period (years), ID, text
- **Confidence Scoring**: Each type detection includes confidence levels
- **Context Awareness**: Column names and data patterns inform type decisions
- **Period Detection**: Automatically identifies year columns (2022, 2023, etc.) as periods
- **Multi-Format Support**: Handles various date formats, currency symbols, and percentage notations

### 📊 Layout Intelligence
Automatically detects and handles different data layouts:

- **Wide Format**: Metrics as columns (Q1, Q2, Q3, Q4 or 2022, 2023, 2024)
- **Long Format**: Time series data with date/period columns
- **Auto-Normalization**: Converts wide format to long format when beneficial
- **Header Detection**: Smart identification of data vs. header rows

### 🧹 Type-Aware Cleaning
Advanced cleaning strategies based on detected column types:

- **Currency Cleaning**: Removes symbols, handles negative values in parentheses
- **Percentage Normalization**: Converts percentages to decimal format
- **Date Standardization**: Consistent date format across the dataset
- **Missing Value Handling**: Type-specific strategies for null values
- **Outlier Detection**: Statistical methods for identifying anomalous values

### 📈 Comprehensive Quality Assessment
Automated data quality evaluation with detailed reporting:

- **Quality Score**: Overall 0-100 quality rating
- **Missing Value Analysis**: Percentage and pattern of missing data
- **Data Type Consistency**: Validation of inferred types across rows
- **Statistical Summary**: Mean, median, std dev, quartiles for numeric data
- **Correlation Matrix**: Relationship analysis between numeric columns

### 🔄 Multi-Sheet Excel Support
Enhanced handling of complex Excel files:

- **Sheet Detection**: Automatically identifies and processes all sheets
- **Individual Processing**: Each sheet processed with its own type inference
- **Combined Results**: Consolidated analysis across all sheets
- **Sheet-Specific Quality**: Individual quality scores per sheet

### ⚡ Performance Optimizations
Efficient processing for large datasets:

- **Chunked Processing**: Memory-efficient handling of large files
- **Streaming Analysis**: Process data without loading entire file into memory
- **Incremental Quality Assessment**: Real-time quality metrics during processing
- **Parallel Processing**: Multi-threaded type inference and cleaning operations

### 🛡️ Robust Error Recovery
Multiple fallback levels ensure reliable processing:

1. **Enhanced Pipeline**: Full type-aware processing
2. **Chunked Processing**: Fallback for memory-intensive datasets
3. **Individual Processing**: Per-column fallback for problematic data
4. **Legacy Processing**: Basic cleaning as final fallback
5. **Error Reporting**: Detailed error logs with specific failure points

### 📋 Complete Audit Trail
Comprehensive logging of all data transformations:

- **Transformation Log**: Step-by-step record of all changes
- **Type Inference Results**: Confidence scores and detection reasoning
- **Quality Metrics**: Before/after quality assessments
- **Error Documentation**: Complete error logs with context
- **Performance Metrics**: Processing time and memory usage tracking

## 🚀 Getting Started

### Prerequisites

- **Python 3.13+** (tested with Python 3.13.1)
- **Node.js 16+** 
- **Google Gemini API key** ([Get one here](https://makersuite.google.com/app/apikey))

### Backend Setup

1. **Clone the repository**:
   ```bash
   git clone https://github.com/fdemirciler/ai-financial-analyst.git
   cd ai-financial-analyst
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
   echo "LLM_PROVIDER=gemini" > .env
   echo "GOOGLE_API_KEY=your_gemini_api_key_here" >> .env
   echo "LLM_MODEL=gemini-2.5-flash" >> .env
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

The application is production-ready with a clean, streamlined codebase. All unnecessary test files and development artifacts have been removed for optimal deployment.

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
- `GOOGLE_API_KEY` - Your Google Gemini API key (required)
- `LLM_PROVIDER` - LLM provider (set to "gemini")
- `LLM_MODEL` - Model name (gemini-2.5-flash)
- `LLM_TEMPERATURE` - Model temperature (default: 0.1)
- `MAX_FILE_SIZE` - Maximum upload size in bytes (default: 52428800 = 50MB)

### Enhanced Pipeline Configuration
The enhanced pipeline includes comprehensive configuration through `backend/config.py`:

```python
# Data Processing Configuration
PIPELINE_CONFIG = {
    "cleaner": {
        "currency_symbols": ["$", "€", "£", "¥", "₹"],
        "percentage_threshold": 0.8,
        "enable_type_conversion": True,
        "handle_missing_values": True
    },
    "profiler": {
        "correlation_threshold": 0.5,
        "outlier_detection_method": "iqr",
        "quality_assessment": True,
        "statistical_summary": True
    },
    "reader": {
        "chunk_size": 1000,
        "encoding_detection": True,
        "skip_empty_rows": True,
        "multi_sheet_support": True
    }
}
```

#### Type Inference Settings
- **Confidence Thresholds**: Minimum confidence for type detection (default: 0.7)
- **Period Detection**: Automatic detection of year columns (2000-2100 range)
- **Currency Detection**: Multi-symbol currency recognition
- **Date Parsing**: Flexible date format detection and parsing

#### Data Quality Assessment
- **Quality Scoring**: Automatic 0-100 quality score calculation
- **Missing Value Analysis**: Comprehensive null value reporting
- **Outlier Detection**: IQR and Z-score based outlier identification
- **Correlation Analysis**: Automatic correlation matrix generation

### Settings
Configuration is managed through `backend/config.py` using Pydantic Settings with environment variable support.

## 🗂️ Project Structure

```
Agent_Workflow_Qwen/
├── backend/
│   ├── __init__.py
│   ├── main.py              # FastAPI application entry point
│   ├── config.py            # Centralized configuration with pipeline settings
│   ├── models.py            # Pydantic models
│   ├── orchestrator.py      # Enhanced orchestration logic
│   ├── session.py           # Enhanced session management
│   ├── logger.py            # Structured logging setup
│   ├── services/
│   │   └── data_processor.py # Enhanced data processing service
│   ├── llm/
│   │   ├── base.py          # LLM base classes
│   │   ├── factory.py       # LLM provider factory
│   │   └── gemini.py        # Google Gemini integration
│   └── tools/
│       ├── __init__.py
│       ├── base.py          # Tool base classes
│       ├── enhanced_tools.py # Enhanced analysis tools with pipeline integration
│       ├── data_cleaner.py  # Legacy data cleaning tool (fallback)
│       ├── data_profiler.py # Legacy data profiling tool (fallback)
│       ├── preprocessor.py  # Legacy data preprocessing tool (fallback)
│       ├── trend_analyzer.py
│       └── variance_analyzer.py
├── pipeline/                # 🆕 Enhanced Data Processing Pipeline
│   ├── __init__.py
│   ├── pipeline.py          # Main pipeline orchestrator
│   ├── type_inferencer.py   # Smart type detection engine
│   ├── layout.py            # Layout detection and normalization
│   ├── cleaner.py           # Type-aware data cleaning
│   ├── profiler.py          # Advanced data profiling and quality assessment
│   ├── audit.py             # Comprehensive audit logging
│   ├── reader.py            # Enhanced file reading with multi-sheet support
│   └── schemas.py           # Pipeline configuration schemas
├── frontend/
│   ├── src/
│   │   ├── components/      # React components
│   │   ├── utils/          # Utility functions
│   │   └── ...
│   ├── package.json
│   └── ...
├── .env                    # Environment configuration
├── requirements.txt        # Python dependencies
├── test_data.csv          # Sample data for testing
├── README.md              # Enhanced documentation
└── CHANGELOG.md           # Version history
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
   - Verify pipeline modules are properly installed

2. **Gemini API errors**:
   - Verify your API key is correct and active
   - Check API quota and billing status

3. **File upload issues**:
   - Ensure file size is under 50MB
   - Supported formats: CSV, XLSX, XLS
   - Check for corrupted or password-protected files

4. **Port conflicts**:
   - Default backend port is 8000, frontend is 5173
   - Change ports in configuration if needed

5. **Enhanced Pipeline Issues**:
   - **Type Inference Errors**: Check data format consistency
   - **Memory Issues**: Large files automatically use chunked processing
   - **Quality Score Problems**: Review missing value patterns
   - **Excel Multi-Sheet Issues**: Verify sheet names and data structure

### Enhanced Pipeline Debugging

**Type Detection Issues**:
```python
# Check type inference results in logs
# Look for confidence scores below 0.7
# Verify period detection for year columns (2022-2100)
```

**Memory Performance**:
- Files >50MB automatically use chunked processing
- Monitor quality scores - low scores may indicate data issues
- Check audit logs for transformation failures

**Data Quality Issues**:
- Quality scores below 60 indicate significant data problems
- Review missing value percentages in pipeline results
- Check correlation matrix for unexpected relationships

### Performance Tips

- For large datasets, the enhanced pipeline automatically optimizes processing
- Use specific queries for better analysis results with type-aware context
- Monitor memory usage - chunked processing activates automatically
- Review audit logs for performance bottlenecks
- Enhanced tools provide better context to LLM for more accurate analysis

### Enhanced Features Validation

**Verify Pipeline is Active**:
- Check logs for "Enhanced pipeline processing" messages
- Confirm type inference results in session data
- Validate quality scores are generated (0-100 scale)
- Review audit trail for transformation steps

## 🔮 Roadmap

### ✅ Completed (v2.0.0 - Enhanced Edition)
- [x] **Advanced Data Processing Pipeline** - Complete type-aware processing system
- [x] **Smart Type Inference** - Semantic type detection with confidence scoring
- [x] **Layout Intelligence** - Wide/long format detection and normalization
- [x] **Type-Aware Data Cleaning** - Intelligent cleaning strategies per data type
- [x] **Comprehensive Data Quality Assessment** - 0-100 quality scoring system
- [x] **Multi-Sheet Excel Support** - Full Excel workbook processing
- [x] **Chunked Processing** - Memory-efficient large file handling
- [x] **Robust Error Recovery** - Multi-level fallback processing
- [x] **Complete Audit Trail** - Full transformation logging and tracking
- [x] **Enhanced Session Management** - Pipeline results storage and retrieval

### 🚧 In Progress
- [ ] **Performance Optimization** - Further memory and speed improvements
- [ ] **Advanced Visualization Integration** - Chart generation from pipeline results
- [ ] **Custom Type Detection** - User-defined semantic types

### 📋 Future Enhancements
- [ ] **Support for more file formats** (JSON, Parquet, XML)
- [ ] **Real-time data streaming** support
- [ ] **Advanced statistical analysis** - Time series, forecasting
- [ ] **Export enhanced analysis results** - PDF, Excel reports with quality metrics
- [ ] **Real-time collaborative analysis** - Multi-user sessions
- [ ] **Custom tool development framework** - User-defined analysis tools
- [ ] **Cloud deployment support** - Docker, Kubernetes, cloud platforms
- [ ] **Data lineage tracking** - Complete data transformation history
- [ ] **Interactive data quality dashboard** - Visual quality assessment tools
- [ ] **Automated data validation rules** - Custom quality checks and alerts

### 🎯 Advanced Features (v3.0)
- [ ] **Machine Learning Integration** - Automated pattern detection and predictions
- [ ] **Natural Language Data Queries** - SQL-like queries in plain English
- [ ] **Data Catalog Integration** - Metadata management and discovery
- [ ] **Enterprise Security Features** - Advanced auth, encryption, audit controls