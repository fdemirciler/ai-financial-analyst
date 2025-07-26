import pandas as pd
import json
import numpy as np
from typing import Dict, Any, List, Optional
from .tools import get_all_tools
from .llm.factory import llm_factory
from .session import session_manager
from .logger import get_logger
from .config import settings

logger = get_logger(__name__)


def convert_numpy_types(obj):
    """Convert numpy types to native Python types for JSON serialization."""
    if isinstance(obj, np.integer):
        return int(obj)
    elif isinstance(obj, np.floating):
        return float(obj)
    elif isinstance(obj, np.ndarray):
        return obj.tolist()
    elif isinstance(obj, dict):
        return {key: convert_numpy_types(value) for key, value in obj.items()}
    elif isinstance(obj, list):
        return [convert_numpy_types(item) for item in obj]
    else:
        return obj


class AnalysisOrchestrator:
    def __init__(self):
        self.tools = get_all_tools()
        self.llm = llm_factory.create_provider(settings.LLM_PROVIDER)

    async def process_file_upload(
        self, session_id: str, file_content: bytes, filename: Optional[str]
    ) -> Dict[str, Any]:
        if not filename:
            raise ValueError("Filename cannot be empty.")

        try:
            # Determine file type and read data
            if filename.lower().endswith(".csv"):
                from io import StringIO

                data = pd.read_csv(StringIO(file_content.decode("utf-8")))
            elif filename.lower().endswith((".xlsx", ".xls")):
                from io import BytesIO

                data = pd.read_excel(BytesIO(file_content))
            else:
                raise ValueError("Unsupported file format")

            logger.info(
                f"Initial data loaded from {filename}. Head:\n{data.head().to_string()}"
            )

            # Store raw data in session
            session_manager.update_session_data(session_id, data)

            # Preprocess data to identify columns to exclude
            preprocess_result = await self.tools["data_preprocessor"].execute(data, {})
            if not preprocess_result.get("success"):
                raise ValueError(
                    f"Data preprocessing failed: {preprocess_result.get('message')}"
                )

            exclude_columns = preprocess_result.get("exclude_columns", [])
            logger.info(
                f"Preprocessor identified {len(exclude_columns)} columns to exclude: {exclude_columns}"
            )

            # Clean data, passing the exclude_columns parameter
            clean_result = await self.tools["data_cleaner"].execute(
                data, {"exclude_columns": exclude_columns}
            )
            logger.info(
                f"Data cleaner tool result:\n{json.dumps(convert_numpy_types(clean_result), indent=2)}"
            )
            if not clean_result.get("success"):
                raise ValueError(f"Data cleaning failed: {clean_result.get('message')}")

            # Convert cleaned data back to DataFrame, ensuring correct types
            cleaned_df = pd.DataFrame(clean_result["data"])
            original_dtypes = clean_result.get("dtypes", {})
            if not cleaned_df.empty and original_dtypes:
                # Convert columns to their original types to ensure consistency
                # This is crucial because JSON serialization loses type information
                cleaned_df = cleaned_df.astype(original_dtypes)

            logger.info(
                f"Reconstructed DataFrame dtypes:\n{cleaned_df.dtypes.to_string()}"
            )
            logger.info(
                f"Reconstructed DataFrame head:\n{cleaned_df.head().to_string()}"
            )

            session_manager.update_session_data(session_id, cleaned_df)

            # Generate comprehensive data profile for LLM
            profile_result = await self.tools["data_profiler"].execute(cleaned_df, {})
            logger.info(
                f"Data profiler tool result:\n{json.dumps(convert_numpy_types(profile_result), indent=2)}"
            )
            session_manager.update_session_metadata(
                session_id, profile_result["profile"]
            )

            return {
                "success": True,
                "message": "File uploaded and processed successfully",
                "data_shape": clean_result["shape"],
                "columns": clean_result["columns"],
            }

        except Exception as e:
            logger.error(
                "Error processing file upload",
                extra={
                    "session_id": session_id,
                    "file_name": filename,
                    "error": str(e),
                },
                exc_info=True,
            )
            raise

    async def process_chat_message(
        self, session_id: str, message: str
    ) -> Dict[str, Any]:
        try:
            # Get session data
            session = session_manager.get_session(session_id)
            if not session:
                raise ValueError("Session not found")

            data = session.get("data")
            metadata = session.get("metadata")

            if data is None:
                raise ValueError("No data available. Please upload a file first.")

            # Build context for LLM
            context = {
                "user_query": message,
                "data_metadata": metadata,
                "conversation_history": session.get("conversation_history", []),
            }

            # Plan tool execution
            tool_plan = await self._plan_tool_execution(context)
            tool_name = tool_plan.get("tool_name")

            if not tool_name or tool_name not in self.tools:
                logger.warning(
                    f"LLM failed to select a valid tool. Selected: '{tool_name}'"
                )
                # Fallback: if no valid tool is selected, generate a response without a tool
                fallback_response = await self._generate_fallback_response(context)
                return {
                    "success": True,
                    "response": fallback_response,
                    "data": None,
                    "tool_used": None,
                }

            # Execute tool
            tool_params = tool_plan.get("parameters", {})
            logger.info(f"Executing tool '{tool_name}' with parameters: {tool_params}")
            logger.info(f"Data passed to tool. Head:\n{data.head().to_string()}")
            logger.info(f"Data dtypes passed to tool:\n{data.dtypes.to_string()}")

            tool_result = await self.tools[tool_name].execute(data, tool_params)
            logger.info(
                f"Tool '{tool_name}' result:\n{json.dumps(convert_numpy_types(tool_result), indent=2)}"
            )

            # Generate final response
            final_response = await self._generate_final_response(context, tool_result)

            # Update conversation history
            session_manager.add_to_history(
                session_id,
                {"role": "user", "content": message},
                {
                    "role": "assistant",
                    "content": final_response,
                    "tool_used": tool_name,
                    "tool_result": tool_result,
                },
            )

            return {
                "success": True,
                "response": final_response,
                "data": tool_result.get("data"),
                "tool_used": tool_name,
                "column_order": tool_result.get("column_order"),
            }
        except Exception as e:
            logger.error(
                "Error processing chat message",
                extra={
                    "session_id": session_id,
                    "user_message": message,
                    "error": str(e),
                },
                exc_info=True,
            )
            raise

    async def _plan_tool_execution(self, context: Dict[str, Any]) -> Dict[str, Any]:
        """
        Uses the LLM to decide which tool to use based on the user's query.
        """
        tool_descriptions = [
            f"- {name}: {tool.description}" for name, tool in self.tools.items()
        ]

        prompt = f"""
        Based on the user's query and the available tools, select the best tool to use.
        
        User Query: "{context['user_query']}"
        
        Available Tools:
        {json.dumps(tool_descriptions, indent=2)}
        
        Data Metadata:
        {json.dumps(convert_numpy_types(context['data_metadata']), indent=2)}
        
        Today's Date: {pd.Timestamp.now().strftime('%Y-%m-%d')}

        Conversation History:
        {json.dumps(convert_numpy_types(context['conversation_history'][-5:]), indent=2)}

        IMPORTANT PERIOD SELECTION RULES:
        - When the user asks for "last two periods" or "recent periods", use the TWO HIGHEST/MOST RECENT period values from the data
        - Available periods from the data: {context['data_metadata'].get('periods', [])}
        - For variance analysis, always compare the LATEST period vs the SECOND-TO-LATEST period
        - Example: if periods are ["2022", "2023", "2024", "2025"], then "last two periods" means period1="2024", period2="2025"

        Respond with a JSON object containing the 'tool_name' and any 'parameters' needed.
        Example: {{"tool_name": "variance_analyzer", "parameters": {{"period1": "2024", "period2": "2025"}}}}
        """

        schema = {
            "type": "object",
            "properties": {
                "tool_name": {
                    "type": "string",
                    "description": "Name of the tool to use.",
                },
                "parameters": {
                    "type": "object",
                    "description": "Parameters for the tool.",
                },
            },
            "required": ["tool_name"],
        }

        try:
            response = await self.llm.generate_structured_response(prompt, schema)
            return response
        except Exception as e:
            logger.error(
                "Error planning tool execution", extra={"error": str(e)}, exc_info=True
            )
            return {}

    async def _generate_final_response(
        self, context: Dict[str, Any], tool_result: Dict[str, Any]
    ) -> str:
        """
        Generates a natural language response based on the tool's output.
        """
        prompt = f"""
        The user asked: "{context['user_query']}"
        
        An analysis tool was run and produced the following result:
        {json.dumps(convert_numpy_types(tool_result), indent=2)}
        
        Based on this result, provide a clear and concise natural language response to the user.
        If the result contains data, summarize it. Do not just repeat the raw data.
        """

        try:
            response = await self.llm.generate_response(
                [{"role": "user", "content": prompt}]
            )
            return response
        except Exception as e:
            logger.error(
                "Error generating final response",
                extra={"error": str(e)},
                exc_info=True,
            )
            return "I encountered an error while generating the final response. Please try again."

    async def _generate_fallback_response(self, context: Dict[str, Any]) -> str:
        """
        Generates a fallback response when no tool is selected.
        """
        prompt = f"""
        The user asked: "{context['user_query']}"

        I was unable to select a specific tool to answer this question. 
        Please provide a helpful response to the user. You can ask for clarification, 
        or explain what kind of questions you can answer based on the available tools.
        
        Available tool descriptions:
        {[tool.description for tool in self.tools.values()]}
        """
        try:
            response = await self.llm.generate_response(
                [{"role": "user", "content": prompt}]
            )
            return response
        except Exception as e:
            logger.error(
                "Error generating fallback response",
                extra={"error": str(e)},
                exc_info=True,
            )
            return "I'm sorry, I couldn't understand your request. Please try rephrasing it."


orchestrator = AnalysisOrchestrator()
