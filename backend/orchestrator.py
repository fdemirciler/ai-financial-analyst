import pandas as pd
import json
import numpy as np
from datetime import datetime, date
from typing import Dict, Any, List, Optional
from .tools import get_all_tools
from .llm.factory import llm_factory
from .session import session_manager
from .logger import get_logger
from .config import settings
from fastapi import APIRouter, UploadFile, File, Form, HTTPException
from .services.data_processor import enhanced_processor, DataProcessingError

logger = get_logger(__name__)


def convert_numpy_types(obj):
    """Convert numpy types and datetime objects to native Python types for JSON serialization."""
    if isinstance(obj, np.integer):
        return int(obj)
    elif isinstance(obj, np.floating):
        return float(obj)
    elif isinstance(obj, np.ndarray):
        return obj.tolist()
    elif isinstance(obj, (datetime, date)):
        return obj.isoformat()
    elif isinstance(obj, pd.Timestamp):
        return obj.isoformat()
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
            logger.info(
                f"Starting enhanced pipeline processing for {filename}",
                extra={
                    "session_id": session_id,
                    "file_size": len(file_content),
                    "filename": filename,
                },
            )

            # Use enhanced processor with new pipeline
            processing_result = await enhanced_processor.process_uploaded_file(
                file_content, filename, session_id
            )

            if processing_result.get("success"):
                # Store pipeline results in session
                pipeline_results = processing_result.get("pipeline_results", [])
                processing_summary = processing_result.get("summary")
                quality_report = processing_result.get("data_quality_report")

                session_manager.store_pipeline_results(
                    session_id, pipeline_results, processing_summary
                )
                if quality_report:
                    session_manager.store_data_quality_report(
                        session_id, quality_report
                    )

                logger.info(
                    f"Enhanced pipeline processing completed successfully for {filename}",
                    extra={
                        "session_id": session_id,
                        "sheets_processed": len(pipeline_results),
                        "quality_score": (
                            quality_report.get("overall_quality_score", 0)
                            if quality_report
                            else 0
                        ),
                    },
                )

                # Return enhanced response
                return {
                    "success": True,
                    "message": processing_result.get(
                        "message", "File processed successfully"
                    ),
                    "data_shape": processing_result.get("processing_info", {}).get(
                        "data_shape", (0, 0)
                    ),
                    "columns": processing_result.get("processing_info", {}).get(
                        "columns", []
                    ),
                    "enhanced_info": {
                        "sheets_processed": len(pipeline_results),
                        "layout_detected": processing_result.get(
                            "processing_info", {}
                        ).get("layout_detected", {}),
                        "data_types": processing_result.get("processing_info", {}).get(
                            "data_types", {}
                        ),
                        "quality_score": (
                            quality_report.get("overall_quality_score", 0)
                            if quality_report
                            else 0
                        ),
                        "processing_summary": processing_summary,
                        "audit_summary": processing_result.get("audit_summary", {}),
                    },
                    "fallback_used": processing_result.get("fallback_used", False),
                }
            else:
                raise ValueError(
                    f"Enhanced processing failed: {processing_result.get('message', 'Unknown error')}"
                )

        except Exception as e:
            logger.error(
                "Enhanced file processing failed, attempting fallback",
                extra={
                    "session_id": session_id,
                    "file_name": filename,
                    "error": str(e),
                },
                exc_info=True,
            )

            # Fallback to a simplified process that still provides a useful response
            try:
                logger.warning(f"Executing simplified fallback for {filename}")
                fallback_result = await enhanced_processor.run_simplified_fallback(
                    file_content, filename
                )

                if fallback_result.get("success"):
                    # Even in fallback, update session with what we have
                    if "data" in fallback_result:
                        session_manager.update_session_data(
                            session_id, fallback_result["data"]
                        )
                    if "profile" in fallback_result:
                        session_manager.update_session_metadata(
                            session_id, fallback_result["profile"]
                        )

                    return {
                        "success": True,  # Success from user's perspective
                        "message": fallback_result.get(
                            "message", "File processed using a fallback method."
                        ),
                        "data_shape": fallback_result.get("shape"),
                        "columns": fallback_result.get("columns"),
                        "enhanced_info": {
                            "quality_score": fallback_result.get("quality_score", 50.0),
                            "processing_summary": {
                                "filename": filename,
                                "sheets_processed": 1,
                                "total_rows": fallback_result.get("shape", [0, 0])[0],
                            },
                        },
                        "fallback_used": True,
                    }
                else:
                    raise DataProcessingError(
                        fallback_result.get("message", "Unknown fallback error")
                    )

            except Exception as fallback_e:
                logger.error(
                    f"Complete file processing failure for {filename}: {fallback_e}",
                    exc_info=True,
                )
                raise HTTPException(
                    status_code=500,
                    detail=f"Could not process file: {fallback_e}",
                )

    async def _fallback_file_processing(
        self, session_id: str, file_content: bytes, filename: str
    ) -> Dict[str, Any]:
        """Fallback to original file processing logic."""
        logger.warning(f"Using fallback file processing for {filename}")

        try:
            # Original processing logic
            if filename.lower().endswith(".csv"):
                from io import StringIO

                data = pd.read_csv(StringIO(file_content.decode("utf-8")))
            elif filename.lower().endswith((".xlsx", ".xls")):
                from io import BytesIO

                data = pd.read_excel(BytesIO(file_content))
            else:
                raise ValueError("Unsupported file format")

            logger.info(
                f"Fallback data loaded from {filename}. Head:\n{data.head().to_string()}"
            )

            # Store raw data in session
            session_manager.update_session_data(session_id, data)

            # Preprocess data to identify columns to exclude (using enhanced tool)
            preprocess_result = await self.tools["data_preprocessor"].execute(data, {})
            if not preprocess_result.get("success"):
                raise ValueError(
                    f"Data preprocessing failed: {preprocess_result.get('message')}"
                )

            exclude_columns = preprocess_result.get("exclude_columns", [])
            logger.info(
                f"Enhanced preprocessor identified {len(exclude_columns)} columns to exclude: {exclude_columns}"
            )
            logger.info(
                f"Type inference results: {preprocess_result.get('type_summary', {})}"
            )

            # Clean data using enhanced cleaner
            clean_result = await self.tools["data_cleaner"].execute(
                data, {"exclude_columns": exclude_columns}
            )
            logger.info(
                f"Enhanced data cleaner tool result:\n{json.dumps(convert_numpy_types(clean_result), indent=2)}"
            )
            if not clean_result.get("success"):
                raise ValueError(f"Data cleaning failed: {clean_result.get('message')}")

            # Convert cleaned data back to DataFrame, ensuring correct types
            cleaned_df = pd.DataFrame(clean_result["data"])
            original_dtypes = clean_result.get("dtypes", {})

            logger.info("🔄 DATA RECONSTRUCTION - Types")
            logger.info(f"    └─ Data types verified for analysis")

            # Apply dtypes safely, handling any conversion errors
            if not cleaned_df.empty and original_dtypes:
                for col, dtype in original_dtypes.items():
                    if col in cleaned_df.columns:
                        try:
                            # Handle special cases for period columns (keep as string)
                            if dtype == "object":
                                cleaned_df[col] = cleaned_df[col].astype(str)
                            else:
                                cleaned_df[col] = cleaned_df[col].astype(dtype)
                        except Exception as e:
                            logger.warning(
                                f"Could not convert column {col} to {dtype}: {e}"
                            )
                            # Keep as is if conversion fails

            logger.info("🔄 DATA RECONSTRUCTION - Preview")
            logger.info(f"    └─ Data structure confirmed")
            logger.info(
                f"Reconstructed DataFrame dtypes:\n{cleaned_df.dtypes.to_string()}"
            )
            logger.info(
                f"Reconstructed DataFrame head:\n{cleaned_df.head().to_string()}"
            )

            logger.info("🔄 SESSION UPDATE - Starting Data Update")
            logger.info(f"    └─ Session ID: {session_id}")
            logger.info(f"    └─ DataFrame shape: {cleaned_df.shape}")
            session_manager.update_session_data(session_id, cleaned_df)
            logger.info("🔄 SESSION UPDATE - Data Update Complete")

            # Generate comprehensive data profile for LLM using enhanced profiler
            logger.info("🔄 DATA PROFILING - Starting Enhanced Profiler")
            logger.info(f"    └─ Available tools: {list(self.tools.keys())}")
            logger.info(
                f"    └─ Profiler tool type: {type(self.tools.get('data_profiler'))}"
            )

            try:
                logger.info("🔄 DATA PROFILING - Executing Enhanced Profiler Tool")
                profile_result = await self.tools["data_profiler"].execute(
                    cleaned_df, {}
                )
                logger.info("🔄 DATA PROFILING - Enhanced Profiler Tool Completed")
                logger.info(f"    └─ Profile result type: {type(profile_result)}")
                logger.info(
                    f"    └─ Profile result keys: {list(profile_result.keys()) if isinstance(profile_result, dict) else 'Not a dict'}"
                )
                logger.info(
                    f"    └─ Profile result success: {profile_result.get('success') if isinstance(profile_result, dict) else 'N/A'}"
                )

                logger.info("🔄 DATA PROFILING - Enhanced")
                logger.info(f"    └─ Advanced profiling completed successfully")
                logger.info(
                    f"Enhanced data profiler tool result:\n{json.dumps(convert_numpy_types(profile_result), indent=2)}"
                )

                logger.info("🔄 SESSION UPDATE - Starting Metadata Update")
                logger.info(
                    f"    └─ Profile data type: {type(profile_result.get('profile'))}"
                )
                session_manager.update_session_metadata(
                    session_id, profile_result["profile"]
                )
                logger.info("🔄 SESSION UPDATE - Metadata Update Complete")

            except Exception as profile_error:
                logger.error(
                    f"🔄 DATA PROFILING - Enhanced Profiler Failed", exc_info=True
                )
                logger.error(f"    └─ Error: {str(profile_error)}")
                logger.error(f"    └─ Error type: {type(profile_error)}")
                logger.warning(
                    f"Enhanced profiling failed, using basic profiling: {profile_error}"
                )
                # Create basic profile as fallback
                logger.info("🔄 DATA PROFILING - Creating Basic Fallback Profile")
                try:
                    basic_profile = {
                        "basic_stats": {
                            "total_rows": len(cleaned_df),
                            "total_columns": len(cleaned_df.columns),
                        },
                        "periods": [],
                        "metrics": [],
                        "columns": list(cleaned_df.columns),
                        "sample_data": cleaned_df.head(3).to_dict("records"),
                    }
                    logger.info("🔄 SESSION UPDATE - Starting Basic Metadata Update")
                    session_manager.update_session_metadata(session_id, basic_profile)
                    logger.info("🔄 DATA PROFILING - Basic Fallback")
                    logger.info(f"    └─ Basic profiling completed as fallback")
                except Exception as fallback_error:
                    logger.error(
                        f"🔄 DATA PROFILING - Basic Fallback Failed: {fallback_error}",
                        exc_info=True,
                    )
                    raise fallback_error

            logger.info("🔄 PROCESSING - Preparing Success Response")
            logger.info(f"    └─ All steps completed successfully")

            return {
                "success": True,
                "message": "File uploaded and processed successfully (fallback method)",
                "data_shape": clean_result["shape"],
                "columns": clean_result["columns"],
                "fallback_used": True,
                "enhanced_info": {
                    "quality_score": 50.0,  # Default score for fallback
                    "processing_summary": {
                        "filename": filename,
                        "sheets_processed": 1,
                        "total_rows": (
                            clean_result["shape"][0] if clean_result.get("shape") else 0
                        ),
                    },
                },
            }

        except Exception as e:
            logger.error(
                "Fallback processing also failed",
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

            # Build enhanced context with pipeline information
            context = self._build_enhanced_context(session, message)

            # Plan tool execution
            tool_plan = await self._plan_tool_execution(context)
            tool_name = tool_plan.get("tool_name")

            if not tool_name or tool_name not in self.tools:
                logger.warning(
                    f"LLM failed to select a valid tool. Selected: '{tool_name}'"
                )
                # Enhanced fallback response with pipeline context
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

            # Generate enhanced final response
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

    def _build_enhanced_context(
        self, session: Dict[str, Any], message: str
    ) -> Dict[str, Any]:
        """Build enhanced context including pipeline results and quality information."""
        pipeline_results = session.get("pipeline_results", [])
        processing_summary = session.get("processing_summary")
        quality_report = session.get("data_quality_report")

        # Extract enhanced metadata from pipeline results
        enhanced_metadata = session.get("metadata", {})

        # Add pipeline-specific information
        if pipeline_results:
            sheets_info = []
            for result in pipeline_results:
                if hasattr(result, "sheet") and hasattr(result, "profile"):
                    sheet_info = {
                        "name": result.sheet,
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
                        "data_types": (
                            {
                                col["name"]: col["dtype"]
                                for col in result.profile.columns
                            }
                            if hasattr(result.profile, "columns")
                            and result.profile.columns
                            else {}
                        ),
                    }
                    sheets_info.append(sheet_info)

            enhanced_metadata["sheets_info"] = sheets_info
            enhanced_metadata["current_sheet"] = session.get("current_sheet")

        return {
            "user_query": message,
            "data_metadata": enhanced_metadata,
            "conversation_history": session.get("conversation_history", []),
            "processing_summary": processing_summary,
            "data_quality_report": quality_report,
            "pipeline_available": len(pipeline_results) > 0,
            "enhanced_features": {
                "multi_sheet_support": len(pipeline_results) > 1,
                "layout_detection": (
                    any(
                        "layout" in str(entry.step)
                        for result in pipeline_results
                        if hasattr(result, "audit")
                        for entry in result.audit.entries
                    )
                    if pipeline_results
                    else False
                ),
                "type_inference": (
                    any(
                        "type_inferencer" in str(entry.step)
                        for result in pipeline_results
                        if hasattr(result, "audit")
                        for entry in result.audit.entries
                    )
                    if pipeline_results
                    else False
                ),
            },
        }

    async def _plan_tool_execution(self, context: Dict[str, Any]) -> Dict[str, Any]:
        """
        Uses the LLM to decide which tool to use based on the user's query with enhanced context.
        """
        tool_descriptions = [
            f"- {name}: {tool.description}" for name, tool in self.tools.items()
        ]

        # Build enhanced context information
        enhanced_info = ""
        if context.get("pipeline_available"):
            enhanced_info += "\n\nEnhanced Processing Available:"
            if context.get("enhanced_features", {}).get("multi_sheet_support"):
                sheets_info = context.get("data_metadata", {}).get("sheets_info", [])
                sheet_names = [sheet["name"] for sheet in sheets_info]
                enhanced_info += f"\n- Multiple sheets available: {sheet_names}"
                enhanced_info += f"\n- Current active sheet: {context.get('data_metadata', {}).get('current_sheet', 'unknown')}"

            if context.get("data_quality_report"):
                quality_score = context["data_quality_report"].get(
                    "overall_quality_score", 0
                )
                enhanced_info += f"\n- Data quality score: {quality_score:.1f}/100"

                issues = context["data_quality_report"].get("issues", [])
                if issues:
                    enhanced_info += f"\n- {len(issues)} data quality issues detected"

            if context.get("enhanced_features", {}).get("layout_detection"):
                enhanced_info += "\n- Smart layout detection was applied"
            if context.get("enhanced_features", {}).get("type_inference"):
                enhanced_info += "\n- Advanced type inference was used"

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
        
        {enhanced_info}

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
        Generates a natural language response based on the tool's output with enhanced context.
        """
        # Extract enhanced information for better response generation
        quality_info = ""
        if context.get("data_quality_report"):
            quality_score = context["data_quality_report"].get(
                "overall_quality_score", 0
            )
            quality_info = f"\n\nData Quality Score: {quality_score:.1f}/100"

            issues = context["data_quality_report"].get("issues", [])
            if issues:
                quality_info += f"\nData Quality Notes: {len(issues)} issues detected"

        processing_info = ""
        if context.get("processing_summary"):
            summary = context["processing_summary"]
            processing_info = f"\n\nProcessed {summary.get('sheets_processed', 1)} sheet(s) with {summary.get('total_rows', 'unknown')} total rows"

        enhanced_context = ""
        if context.get("enhanced_features", {}).get("layout_detection"):
            enhanced_context += "\n- Advanced layout detection was used"
        if context.get("enhanced_features", {}).get("type_inference"):
            enhanced_context += "\n- Smart data type inference was applied"
        if context.get("enhanced_features", {}).get("multi_sheet_support"):
            enhanced_context += "\n- Multi-sheet analysis capability available"

        prompt = f"""
        The user asked: "{context['user_query']}"
        
        An analysis tool was run and produced the following result:
        {json.dumps(convert_numpy_types(tool_result), indent=2)}
        
        Additional Context:
        {quality_info}
        {processing_info}
        
        Enhanced Processing Features:{enhanced_context}
        
        Provide a clear, professional response in **markdown format** following these guidelines:
        - Use ## for main section headers (e.g., ## Analysis Results)
        - Use ### for subsections (e.g., ### Key Findings)
        - Use **bold** for important metrics and values
        - Use bullet points (*) for lists
        - Use tables when comparing multiple items
        - Include specific numbers and percentages in **bold**
        - End with actionable insights or recommendations
        - If data quality issues were detected, mention them appropriately
        
        Format your response as markdown text.
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
