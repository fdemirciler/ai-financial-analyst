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
