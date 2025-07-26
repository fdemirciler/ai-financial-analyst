import logging
import sys
import json
from pythonjsonlogger import jsonlogger


class HumanReadableFormatter(logging.Formatter):
    """
    Custom formatter to make logs more human-readable for data flow understanding.
    """

    def format(self, record):
        # Extract basic info
        timestamp = self.formatTime(record, "%H:%M:%S")
        level = record.levelname
        name = record.name.split(".")[-1]  # Get just the module name
        message = record.getMessage()

        # Start with basic format
        formatted = f"[{timestamp}] {level} {name.upper()}: "

        # Special formatting for different types of messages
        if "File upload request" in message:
            formatted += "📁 FILE UPLOAD STARTED"
            file_name = getattr(record, "file_name", None)
            if file_name:
                formatted += f" - File: {file_name}"

        elif "Initial data loaded" in message:
            formatted += "📊 RAW DATA LOADED"
            if "Head:" in message:
                # Extract and format the data preview
                lines = message.split("\n")
                formatted += f"\n    └─ Shape: {lines[1].strip() if len(lines) > 1 else 'Unknown'}"
                formatted += f"\n    └─ Preview: First 5 rows shown"

        elif "Preprocessor identified" in message:
            formatted += "🔧 DATA PREPROCESSING"
            if "columns to exclude" in message:
                # Extract excluded columns
                start = message.find("[")
                end = message.find("]")
                if start != -1 and end != -1:
                    excluded = message[start : end + 1]
                    formatted += f"\n    └─ Excluded columns: {excluded}"

        elif "Data cleaner tool result" in message:
            formatted += "🧹 DATA CLEANING COMPLETED"
            try:
                # Try to parse the JSON result
                start = message.find("{")
                if start != -1:
                    json_data = json.loads(message[start:])
                    if json_data.get("success"):
                        shape = json_data.get("shape", [])
                        if len(shape) >= 2:
                            formatted += f"\n    └─ Clean data shape: {shape[0]} rows × {shape[1]} columns"
                        if "Total Assets" in str(json_data.get("data", [])):
                            formatted += (
                                f"\n    └─ ✅ Total Assets data found and cleaned"
                            )
            except:
                formatted += "\n    └─ Processing completed"

        elif "Reconstructed DataFrame" in message:
            if "dtypes:" in message:
                formatted += "🔄 DATA RECONSTRUCTION - Types"
                formatted += f"\n    └─ Data types verified for analysis"
            elif "head:" in message:
                formatted += "🔄 DATA RECONSTRUCTION - Preview"
                formatted += f"\n    └─ Data structure confirmed"

        elif "Data profiler tool result" in message:
            formatted += "📋 DATA PROFILING COMPLETED"
            try:
                start = message.find("{")
                if start != -1:
                    json_data = json.loads(message[start:])
                    profile = json_data.get("profile", {})
                    basic_stats = profile.get("basic_stats", {})
                    rows = basic_stats.get("rows", "Unknown")
                    cols = basic_stats.get("columns", "Unknown")
                    periods = profile.get("periods", [])
                    metrics = profile.get("metrics", [])

                    formatted += f"\n    └─ Dataset: {rows} financial metrics × {cols} time periods"
                    formatted += f"\n    └─ Time periods: {periods}"
                    formatted += f"\n    └─ Key metrics found: {len(metrics)} items"
                    if "Total Assets" in metrics:
                        formatted += f"\n    └─ ✅ Total Assets metric confirmed"
            except:
                formatted += f"\n    └─ Profiling completed"

        elif "File uploaded successfully" in message:
            formatted += "✅ FILE UPLOAD SUCCESSFUL"
            data_shape = getattr(record, "data_shape", None)
            if data_shape:
                formatted += f"\n    └─ Final dataset: {data_shape[0]} rows × {data_shape[1]} columns"

        elif "Chat request received" in message:
            formatted += "💬 USER REQUEST RECEIVED"
            user_message = getattr(record, "user_message", None)
            if user_message:
                user_msg = (
                    user_message[:50] + "..."
                    if len(user_message) > 50
                    else user_message
                )
                formatted += f'\n    └─ Query: "{user_msg}"'

        elif "Executing tool" in message:
            formatted += "🔧 TOOL EXECUTION STARTED"
            if "trend_analyzer" in message:
                formatted += " - TREND ANALYZER"
                # Extract parameters
                start = message.find("parameters:")
                if start != -1:
                    param_text = message[start:]
                    if "Total Assets" in param_text:
                        formatted += f"\n    └─ 🎯 Target metric: Total Assets"
            elif "variance_analyzer" in message:
                formatted += " - VARIANCE ANALYZER"
            else:
                tool_name = message.split("'")[1] if "'" in message else "Unknown"
                formatted += f" - {tool_name.upper()}"

        elif "Data passed to tool" in message:
            formatted += "📤 DATA SENT TO TOOL"
            if "Head:" in message:
                formatted += f"\n    └─ Sample data provided for analysis"

        elif "Tool" in message and "result:" in message:
            formatted += "📥 TOOL RESULT RECEIVED"
            if "trend_analyzer" in message:
                formatted += " - TREND ANALYZER"
                try:
                    # Parse the result to show key findings
                    start = message.find("{")
                    if start != -1:
                        json_data = json.loads(message[start:])
                        if json_data.get("success"):
                            metric = json_data.get("metric", "Unknown")
                            values = json_data.get("values", [])
                            overall = json_data.get("overall_trend", {})

                            formatted += (
                                f"\n    └─ ✅ Analysis successful for: {metric}"
                            )
                            if values:
                                first_val = values[0].get("value", 0)
                                last_val = values[-1].get("value", 0)
                                formatted += f"\n    └─ 📈 Values: {first_val:,.0f} → {last_val:,.0f}"

                            trend = overall.get("trend", "unknown")
                            total_change_pct = overall.get("total_change_percentage", 0)
                            formatted += f"\n    └─ 📊 Overall trend: {trend.upper()} ({total_change_pct:+.1f}%)"
                except:
                    formatted += f"\n    └─ Analysis completed"

        elif "Chat response generated" in message:
            formatted += "✅ RESPONSE GENERATED"
            success = getattr(record, "success", None)
            if success:
                formatted += " - SUCCESS"
                tool_used = getattr(record, "tool_used", None)
                if tool_used:
                    formatted += f"\n    └─ Used tool: {tool_used}"

        else:
            # Default formatting for other messages
            formatted += message

        return formatted


def get_logger(name: str) -> logging.Logger:
    """
    Configures and returns a human-readable logger for data flow tracking.
    """
    logger = logging.getLogger(name)
    logger.setLevel(logging.INFO)

    # Prevent duplicate handlers
    if logger.hasHandlers():
        logger.handlers.clear()

    log_handler = logging.StreamHandler(sys.stdout)

    # Use human-readable formatter for better data flow understanding
    formatter = HumanReadableFormatter()
    log_handler.setFormatter(formatter)
    logger.addHandler(log_handler)
    logger.propagate = False
    return logger


logger = get_logger(__name__)
