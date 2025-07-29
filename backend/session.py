import json
from typing import Dict, Any, Optional, List
from datetime import datetime, timedelta


class SessionManager:
    def __init__(self):
        self.sessions: Dict[str, Dict[str, Any]] = {}

    def create_session(self, session_id: str) -> None:
        self.sessions[session_id] = {
            "created_at": datetime.now(),
            "data": None,
            "metadata": None,
            "conversation_history": [],
            "tool_results": {},
            # Enhanced pipeline support
            "pipeline_results": [],
            "current_sheet": None,
            "processing_summary": None,
            "data_quality_report": None,
        }

    def get_session(self, session_id: str) -> Optional[Dict[str, Any]]:
        if session_id in self.sessions:
            # Check if session is still valid (not expired)
            session = self.sessions[session_id]
            if datetime.now() - session["created_at"] < timedelta(hours=1):
                return session
            else:
                # Session expired, remove it
                del self.sessions[session_id]
        return None

    def update_session_data(self, session_id: str, data: Any) -> bool:
        session = self.get_session(session_id)
        if session:
            session["data"] = data
            return True
        return False

    def update_session_metadata(
        self, session_id: str, metadata: Dict[str, Any]
    ) -> bool:
        session = self.get_session(session_id)
        if session:
            session["metadata"] = metadata
            return True
        return False

    def store_pipeline_results(
        self,
        session_id: str,
        results: List[Any],
        summary: Optional[Dict[str, Any]] = None,
    ) -> bool:
        """Store pipeline results and processing summary."""
        session = self.get_session(session_id)
        if session:
            session["pipeline_results"] = results
            session["processing_summary"] = summary

            # Set primary data to first result's clean data for backward compatibility
            if results and hasattr(results[0], "clean_data"):
                # Convert long format back to DataFrame for tools compatibility
                import pandas as pd

                primary_data = pd.DataFrame(results[0].clean_data)
                session["data"] = primary_data

                # Update metadata from profile
                if hasattr(results[0], "profile"):
                    session["metadata"] = {
                        "basic_stats": (
                            results[0].profile.basic_stats
                            if hasattr(results[0].profile, "basic_stats")
                            else {}
                        ),
                        "periods": (
                            results[0].profile.periods
                            if hasattr(results[0].profile, "periods")
                            else []
                        ),
                        "metrics": (
                            results[0].profile.metrics
                            if hasattr(results[0].profile, "metrics")
                            else []
                        ),
                        "columns": (
                            results[0].profile.columns
                            if hasattr(results[0].profile, "columns")
                            else []
                        ),
                    }

                # Set current sheet to first sheet
                session["current_sheet"] = (
                    results[0].sheet if hasattr(results[0], "sheet") else None
                )

            return True
        return False

    def store_data_quality_report(
        self, session_id: str, quality_report: Dict[str, Any]
    ) -> bool:
        """Store data quality report."""
        session = self.get_session(session_id)
        if session:
            session["data_quality_report"] = quality_report
            return True
        return False

    def get_pipeline_results(self, session_id: str) -> List[Any]:
        """Get stored pipeline results."""
        session = self.get_session(session_id)
        if session:
            return session.get("pipeline_results", [])
        return []

    def get_processing_summary(self, session_id: str) -> Optional[Dict[str, Any]]:
        """Get processing summary."""
        session = self.get_session(session_id)
        if session:
            return session.get("processing_summary")
        return None

    def get_data_quality_report(self, session_id: str) -> Optional[Dict[str, Any]]:
        """Get data quality report."""
        session = self.get_session(session_id)
        if session:
            return session.get("data_quality_report")
        return None

    def set_current_sheet(self, session_id: str, sheet_name: str) -> bool:
        """Set the current active sheet for analysis."""
        session = self.get_session(session_id)
        if session:
            pipeline_results = session.get("pipeline_results", [])
            # Find the sheet and set it as current data
            for result in pipeline_results:
                if hasattr(result, "sheet") and result.sheet == sheet_name:
                    import pandas as pd

                    session["data"] = pd.DataFrame(result.clean_data)
                    session["current_sheet"] = sheet_name

                    # Update metadata for current sheet
                    if hasattr(result, "profile"):
                        session["metadata"] = {
                            "basic_stats": (
                                result.profile.basic_stats
                                if hasattr(result.profile, "basic_stats")
                                else {}
                            ),
                            "periods": (
                                result.profile.periods
                                if hasattr(result.profile, "periods")
                                else []
                            ),
                            "metrics": (
                                result.profile.metrics
                                if hasattr(result.profile, "metrics")
                                else []
                            ),
                            "columns": (
                                result.profile.columns
                                if hasattr(result.profile, "columns")
                                else []
                            ),
                        }
                    return True
            return False
        return False

    def add_to_history(
        self,
        session_id: str,
        user_message: Dict[str, Any],
        assistant_message: Dict[str, Any],
    ) -> bool:
        session = self.get_session(session_id)
        if session:
            session["conversation_history"].append(user_message)
            session["conversation_history"].append(assistant_message)
            return True
        return False

    def get_conversation_history(self, session_id: str) -> List[Dict[str, Any]]:
        session = self.get_session(session_id)
        if session:
            return session["conversation_history"]
        return []

    def store_tool_result(self, session_id: str, tool_name: str, result: Any) -> bool:
        session = self.get_session(session_id)
        if session:
            session["tool_results"][tool_name] = result
            return True
        return False

    def get_tool_result(self, session_id: str, tool_name: str) -> Any:
        session = self.get_session(session_id)
        if session and tool_name in session["tool_results"]:
            return session["tool_results"][tool_name]
        return None


session_manager = SessionManager()
