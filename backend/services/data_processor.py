"""Enhanced data processing service using the new pipeline architecture.

This service provides a high-level interface for data processing operations,
integrating the new pipeline while maintaining compatibility with existing workflows.
"""

from __future__ import annotations

import tempfile
from io import BytesIO, StringIO
from pathlib import Path
from typing import Dict, Any, List, Tuple, Optional, Union
import pandas as pd

from pipeline import Pipeline
from pipeline.schemas import PipelineResult, PipelineConfig, AuditTrail
from ..logger import get_logger
from ..config import settings

logger = get_logger(__name__)


class DataProcessingError(Exception):
    """Custom exception for data processing errors."""

    pass


class ChunkedProcessor:
    """Handles chunked processing for large datasets."""

    def __init__(self, chunk_size: Optional[int] = None):
        self.chunk_size = chunk_size or settings.CHUNK_SIZE

    def process_large_dataframe(
        self, df: pd.DataFrame, config: PipelineConfig
    ) -> List[PipelineResult]:
        """Process large DataFrame in chunks if needed."""
        if len(df) * len(df.columns) * 8 < self.chunk_size:  # Rough memory estimate
            # Small enough to process normally
            pipeline = Pipeline(config)
            return pipeline._run([("data", df, self._create_meta(df, "chunked_data"))])

        # Process in chunks
        chunk_results = []
        chunk_size_rows = max(1, self.chunk_size // (len(df.columns) * 8))

        for i in range(0, len(df), chunk_size_rows):
            chunk = df.iloc[i : i + chunk_size_rows].copy()
            pipeline = Pipeline(config)
            chunk_result = pipeline._run(
                [
                    (
                        f"chunk_{i//chunk_size_rows + 1}",
                        chunk,
                        self._create_meta(chunk, f"chunk_{i//chunk_size_rows + 1}"),
                    )
                ]
            )
            chunk_results.extend(chunk_result)

        return chunk_results

    def _create_meta(self, df: pd.DataFrame, sheet_name: str):
        """Create metadata for chunk processing."""
        from pipeline.schemas import SheetMeta

        return SheetMeta(
            source_path="memory", sheet=sheet_name, nrows=len(df), ncols=len(df.columns)
        )


class EnhancedDataProcessor:
    """Enhanced data processor using the new pipeline architecture."""

    def __init__(self, config: Optional[PipelineConfig] = None):
        """Initialize the processor with a pipeline configuration."""
        try:
            self.config = config or settings.pipeline_config
            self.chunked_processor = ChunkedProcessor()
            logger.info(
                "EnhancedDataProcessor initialized successfully",
                extra={"config": self.config.model_dump()},
            )
        except Exception as e:
            logger.error(
                "Failed to initialize EnhancedDataProcessor",
                exc_info=True,
            )
            # Re-raise to ensure the application doesn't start with a faulty processor
            raise e

    async def process_uploaded_file(
        self, file_content: bytes, filename: str, session_id: str
    ) -> Dict[str, Any]:
        """Process uploaded file using the enhanced pipeline."""
        logger.info(
            f"Enhanced processor starting for {filename} with session {session_id}"
        )
        try:
            # Determine file type and create temporary file
            logger.info(f"Creating temporary file for {filename}")
            temp_path = self._create_temp_file(file_content, filename)
            logger.info(f"Temporary file created at {temp_path}")

            try:
                # Process file based on type
                if filename.lower().endswith(".csv"):
                    logger.info(f"Processing CSV file: {filename}")
                    results = await self._process_csv(temp_path)
                elif filename.lower().endswith((".xlsx", ".xls")):
                    logger.info(f"Processing Excel file: {filename}")
                    results = await self._process_excel(temp_path)
                else:
                    raise DataProcessingError(f"Unsupported file format: {filename}")

                logger.info(f"File processing completed, {len(results)} results")

                # Generate processing summary
                summary = self._generate_processing_summary(results, filename)

                # Enhanced response with pipeline information
                return {
                    "success": True,
                    "message": "File processed successfully with enhanced pipeline",
                    "pipeline_results": results,
                    "summary": summary,
                    "processing_info": self._extract_processing_info(results),
                    "data_quality_report": self._generate_quality_report(results),
                    "audit_summary": self._summarize_audit_trails(results),
                }

            finally:
                # Clean up temporary file
                logger.info(f"Cleaning up temporary file: {temp_path}")
                temp_path.unlink(missing_ok=True)

        except Exception as e:
            logger.error(
                f"Enhanced processing failed for {filename}: {e}", exc_info=True
            )
            # Try a more basic fallback first before giving up
            try:
                # Fallback: try basic processing without the full pipeline
                return await self._basic_pipeline_fallback(file_content, filename)
            except Exception as fallback_error:
                logger.error(f"Basic pipeline fallback also failed: {fallback_error}")
                # Final fallback to basic processing
                return await self._fallback_processing(file_content, filename)

    async def _process_csv(self, temp_path: Path) -> List[PipelineResult]:
        """Process CSV file with error handling."""
        try:
            logger.info(f"Creating pipeline with config: {self.config}")
            pipeline = Pipeline(self.config)
            logger.info(f"Running pipeline from CSV: {temp_path}")
            result = pipeline.run_from_csv(temp_path)
            logger.info(f"Pipeline completed successfully with {len(result)} results")
            return result
        except Exception as e:
            logger.error(f"Pipeline CSV processing failed: {e}", exc_info=True)
            logger.warning(
                f"Pipeline CSV processing failed: {e}, attempting chunked processing"
            )
            # Try chunked processing for large files
            df = pd.read_csv(temp_path)
            return self.chunked_processor.process_large_dataframe(df, self.config)

    async def _process_excel(self, temp_path: Path) -> List[PipelineResult]:
        """Process Excel file with multi-sheet support and error handling."""
        successful_results = []
        processing_errors = []

        try:
            pipeline = Pipeline(self.config)
            all_results = pipeline.run_from_excel(temp_path)

            # Separate successful and failed results
            for result in all_results:
                if hasattr(result, "clean_data") and result.clean_data is not None:
                    successful_results.append(result)
                else:
                    processing_errors.append(
                        {
                            "sheet": (
                                result.sheet if hasattr(result, "sheet") else "unknown"
                            ),
                            "error": "Failed to process sheet data",
                        }
                    )

        except Exception as e:
            logger.warning(
                f"Pipeline Excel processing failed: {e}, attempting sheet-by-sheet processing"
            )
            # Process sheets individually for better error recovery
            successful_results, processing_errors = (
                await self._process_excel_sheets_individually(temp_path)
            )

        # If we have any successful results, return them with error summary
        if successful_results:
            # Add error information to the first result's audit trail
            if processing_errors:
                for result in successful_results:
                    result.audit.entries.append(
                        self._create_error_audit_entry(processing_errors)
                    )
            return successful_results
        else:
            raise DataProcessingError(
                f"Failed to process any sheets. Errors: {processing_errors}"
            )

    async def _process_excel_sheets_individually(
        self, temp_path: Path
    ) -> Tuple[List[PipelineResult], List[Dict]]:
        """Process Excel sheets one by one for better error recovery."""
        successful_results = []
        processing_errors = []

        try:
            # Read Excel file to get sheet names
            xls_file = pd.ExcelFile(temp_path)

            for sheet_name in xls_file.sheet_names:
                try:
                    # Read individual sheet
                    df = pd.read_excel(temp_path, sheet_name=sheet_name)

                    # Process with chunked processor if needed
                    sheet_results = self.chunked_processor.process_large_dataframe(
                        df, self.config
                    )

                    # Update sheet names in results
                    for result in sheet_results:
                        # Create new result with updated sheet name
                        updated_result = PipelineResult(
                            sheet=str(sheet_name),
                            meta=result.meta,
                            clean_data=result.clean_data,
                            profile=result.profile,
                            audit=result.audit,
                        )
                        # Update meta sheet name too
                        updated_result.meta.sheet = str(sheet_name)
                        successful_results.append(updated_result)

                except Exception as e:
                    logger.error(f"Failed to process sheet {sheet_name}: {e}")
                    processing_errors.append({"sheet": sheet_name, "error": str(e)})

        except Exception as e:
            logger.error(f"Failed to read Excel file structure: {e}")
            processing_errors.append(
                {
                    "sheet": "file_structure",
                    "error": f"Could not read Excel file: {str(e)}",
                }
            )

        return successful_results, processing_errors

    def _create_temp_file(self, file_content: bytes, filename: str) -> Path:
        """Create temporary file for processing."""
        suffix = Path(filename).suffix
        temp_file = tempfile.NamedTemporaryFile(suffix=suffix, delete=False)
        temp_file.write(file_content)
        temp_file.close()
        return Path(temp_file.name)

    def _generate_processing_summary(
        self, results: List[PipelineResult], filename: str
    ) -> Dict[str, Any]:
        """Generate a summary of processing results."""
        total_rows = sum(len(result.clean_data) for result in results)
        total_sheets = len(results)

        return {
            "filename": filename,
            "sheets_processed": total_sheets,
            "total_rows": total_rows,
            "sheets": [
                {
                    "name": result.sheet,
                    "rows": len(result.clean_data),
                    "columns": (
                        len(result.profile.columns) if result.profile.columns else 0
                    ),
                    "data_quality_score": self._calculate_sheet_quality_score(result),
                }
                for result in results
            ],
        }

    def _extract_processing_info(self, results: List[PipelineResult]) -> Dict[str, Any]:
        """Extract processing information for API response."""
        if not results:
            return {"error": "No results to process"}

        # Use first result as primary (most common case is single sheet)
        primary_result = results[0]

        return {
            "data_shape": (
                len(primary_result.clean_data),
                (
                    len(primary_result.profile.columns)
                    if primary_result.profile.columns
                    else 0
                ),
            ),
            "columns": (
                [col["name"] for col in primary_result.profile.columns]
                if primary_result.profile.columns
                else []
            ),
            "periods": (
                primary_result.profile.periods
                if hasattr(primary_result.profile, "periods")
                else []
            ),
            "metrics": (
                primary_result.profile.metrics
                if hasattr(primary_result.profile, "metrics")
                else []
            ),
            "layout_detected": self._extract_layout_info(primary_result),
            "data_types": (
                {col["name"]: col["dtype"] for col in primary_result.profile.columns}
                if primary_result.profile.columns
                else {}
            ),
        }

    def _generate_quality_report(self, results: List[PipelineResult]) -> Dict[str, Any]:
        """Generate comprehensive data quality report."""
        quality_scores = []
        issues = []

        for result in results:
            sheet_score = self._calculate_sheet_quality_score(result)
            quality_scores.append(sheet_score)

            # Check for data quality issues
            sheet_issues = self._identify_quality_issues(result)
            if sheet_issues:
                issues.extend(
                    [{**issue, "sheet": result.sheet} for issue in sheet_issues]
                )

        overall_score = (
            sum(quality_scores) / len(quality_scores) if quality_scores else 0
        )

        return {
            "overall_quality_score": round(overall_score, 2),
            "sheet_scores": {
                result.sheet: score for result, score in zip(results, quality_scores)
            },
            "issues": issues,
            "recommendations": self._generate_quality_recommendations(issues),
        }

    def _calculate_sheet_quality_score(self, result: PipelineResult) -> float:
        """Calculate quality score for a sheet (0-100)."""
        if not result.profile.columns:
            return 0.0

        score = 100.0

        # Penalize for missing values
        for col in result.profile.columns:
            null_count = col.get("null_count", 0)
            total_rows = len(result.clean_data)
            if total_rows > 0:
                null_ratio = null_count / total_rows
                score -= (
                    null_ratio * 20
                )  # Max 20 point penalty for completely null columns

        # Bonus for having good data variety
        unique_counts = [col.get("unique_count", 0) for col in result.profile.columns]
        if unique_counts and max(unique_counts) > 1:
            score += 10  # Bonus for data variety

        return max(0.0, min(100.0, score))

    def _identify_quality_issues(self, result: PipelineResult) -> List[Dict[str, Any]]:
        """Identify data quality issues in a sheet."""
        issues = []

        if not result.profile.columns:
            issues.append(
                {
                    "type": "no_columns",
                    "severity": "high",
                    "message": "No columns detected in data",
                }
            )
            return issues

        for col in result.profile.columns:
            # High null percentage
            null_count = col.get("null_count", 0)
            total_rows = len(result.clean_data)
            if total_rows > 0:
                null_ratio = null_count / total_rows
                if null_ratio > 0.5:
                    issues.append(
                        {
                            "type": "high_null_rate",
                            "severity": "medium",
                            "column": col["name"],
                            "message": f"Column {col['name']} has {null_ratio:.1%} missing values",
                        }
                    )

            # Low unique count for non-ID columns
            unique_count = col.get("unique_count", 0)
            if unique_count == 1 and total_rows > 1:
                issues.append(
                    {
                        "type": "constant_column",
                        "severity": "low",
                        "column": col["name"],
                        "message": f"Column {col['name']} has constant values",
                    }
                )

        return issues

    def _generate_quality_recommendations(
        self, issues: List[Dict[str, Any]]
    ) -> List[str]:
        """Generate recommendations based on quality issues."""
        recommendations = []

        high_null_columns = [
            issue["column"] for issue in issues if issue["type"] == "high_null_rate"
        ]
        if high_null_columns:
            recommendations.append(
                f"Consider removing or imputing high-null columns: {', '.join(high_null_columns)}"
            )

        constant_columns = [
            issue["column"] for issue in issues if issue["type"] == "constant_column"
        ]
        if constant_columns:
            recommendations.append(
                f"Consider removing constant columns: {', '.join(constant_columns)}"
            )

        if not recommendations:
            recommendations.append("Data quality looks good!")

        return recommendations

    def _extract_layout_info(self, result: PipelineResult) -> Dict[str, Any]:
        """Extract layout detection information from audit trail."""
        layout_info = {"detected": "unknown", "confidence": 0.0}

        for entry in result.audit.entries:
            if entry.step == "layout" and entry.action == "detect":
                layout_info.update(entry.details)
                break

        return layout_info

    def _summarize_audit_trails(self, results: List[PipelineResult]) -> Dict[str, Any]:
        """Summarize audit trails from all results."""
        all_steps = []

        for result in results:
            for entry in result.audit.entries:
                all_steps.append(
                    {
                        "sheet": result.sheet,
                        "step": entry.step,
                        "action": entry.action,
                        "rows_affected": entry.rows_affected,
                        "timestamp": entry.timestamp,
                    }
                )

        # Group by step type
        step_summary = {}
        for step in all_steps:
            step_type = step["step"]
            if step_type not in step_summary:
                step_summary[step_type] = {"count": 0, "total_rows_affected": 0}
            step_summary[step_type]["count"] += 1
            if step["rows_affected"]:
                step_summary[step_type]["total_rows_affected"] += step["rows_affected"]

        return {
            "total_operations": len(all_steps),
            "step_summary": step_summary,
            "processing_time": self._calculate_processing_duration(all_steps),
        }

    def _calculate_processing_duration(self, steps: List[Dict]) -> float:
        """Calculate total processing duration from audit steps."""
        if not steps:
            return 0.0

        timestamps = [step["timestamp"] for step in steps if step["timestamp"]]
        if len(timestamps) < 2:
            return 0.0

        start_time = min(timestamps)
        end_time = max(timestamps)
        return (end_time - start_time).total_seconds()

    def _create_error_audit_entry(self, errors: List[Dict]):
        """Create audit entry for processing errors."""
        from pipeline.schemas import AuditEntry
        from datetime import datetime

        return AuditEntry(
            step="error_recovery",
            action="sheet_processing_errors",
            details={"errors": errors},
            timestamp=datetime.utcnow(),
        )

    async def _basic_pipeline_fallback(
        self, file_content: bytes, filename: str
    ) -> Dict[str, Any]:
        """Basic processing fallback that uses legacy tools."""
        logger.warning(f"Using basic pipeline fallback for {filename}")

        try:
            # Load data using basic pandas
            if filename.lower().endswith(".csv"):
                df = pd.read_csv(StringIO(file_content.decode("utf-8")))
            elif filename.lower().endswith((".xlsx", ".xls")):
                df = pd.read_excel(BytesIO(file_content))
            else:
                raise DataProcessingError(f"Unsupported file format: {filename}")

            # Use enhanced tools but with simpler processing
            from ..tools import get_all_tools

            tools = get_all_tools()

            # Use enhanced preprocessor
            preprocess_result = await tools["data_preprocessor"].execute(df, {})
            exclude_columns = preprocess_result.get("exclude_columns", [])

            # Use enhanced cleaner with exclude columns
            clean_result = await tools["data_cleaner"].execute(
                df, {"exclude_columns": exclude_columns}
            )

            if clean_result.get("success"):
                # Create a simple profile
                profile_result = await tools["data_profiler"].execute(df, {})

                return {
                    "success": True,
                    "message": "File processed with basic enhanced pipeline",
                    "processing_info": {
                        "data_shape": clean_result.get("shape", df.shape),
                        "columns": clean_result.get("columns", df.columns.tolist()),
                        "data_types": clean_result.get("dtypes", {}),
                        "types_detected": clean_result.get("types_detected", {}),
                    },
                    "data_quality_report": {
                        "overall_quality_score": 75.0,  # Default score for basic processing
                        "issues": [],
                        "recommendations": ["Data processed with basic enhanced tools"],
                    },
                    "fallback_used": True,
                    "fallback_type": "basic_enhanced",
                }
            else:
                raise DataProcessingError("Enhanced tools failed")

        except Exception as e:
            logger.error(f"Basic pipeline fallback failed for {filename}: {e}")
            raise

    async def _fallback_processing(
        self, file_content: bytes, filename: str
    ) -> Dict[str, Any]:
        """Fallback to basic processing if pipeline fails completely."""
        logger.warning(f"Using fallback processing for {filename}")

        try:
            # Basic pandas processing as fallback
            if filename.lower().endswith(".csv"):
                df = pd.read_csv(StringIO(file_content.decode("utf-8")))
            elif filename.lower().endswith((".xlsx", ".xls")):
                df = pd.read_excel(BytesIO(file_content))
            else:
                raise DataProcessingError(f"Unsupported file format: {filename}")

            return {
                "success": True,
                "message": "File processed with basic fallback method",
                "fallback_used": True,
                "processing_info": {
                    "data_shape": df.shape,
                    "columns": df.columns.tolist(),
                    "data_types": df.dtypes.astype(str).to_dict(),
                },
                "data_quality_report": {
                    "overall_quality_score": 50.0,  # Default fallback score
                    "issues": ["Pipeline processing failed, using basic processing"],
                    "recommendations": ["Review data format and try uploading again"],
                },
            }

        except Exception as e:
            logger.error(f"Fallback processing also failed for {filename}: {e}")
            raise DataProcessingError(f"Complete processing failure: {str(e)}")

    async def run_simplified_fallback(
        self, file_content: bytes, filename: str
    ) -> Dict[str, Any]:
        """
        Run a simplified fallback that reads the data and provides a basic profile.
        This is a last resort when the main pipeline fails.
        """
        logger.warning(f"Running simplified fallback for {filename}")
        df = self._read_file_content_to_dataframe(file_content, filename)

        if df is None:
            return {
                "success": False,
                "message": "File could not be read, even with fallback methods.",
            }

        # Basic profile
        profile = {
            "basic_stats": {
                "total_rows": len(df),
                "total_columns": len(df.columns),
            },
            "columns": list(df.columns),
            "sample_data": df.head(3).to_dict("records"),
        }

        return {
            "success": True,
            "message": "File read successfully using simplified fallback.",
            "data": df,
            "profile": profile,
            "shape": df.shape,
            "columns": list(df.columns),
            "quality_score": 40.0,  # Lower score indicating fallback
        }

    def _read_file_content_to_dataframe(
        self, file_content: bytes, filename: str
    ) -> Optional[pd.DataFrame]:
        """Read file content into a pandas DataFrame, supporting multiple encodings for CSV."""
        try:
            if filename.lower().endswith(".csv"):
                # Try standard utf-8 first
                try:
                    return pd.read_csv(BytesIO(file_content))
                except UnicodeDecodeError:
                    logger.warning("UTF-8 decoding failed, trying latin-1.")
                    # Fallback to latin-1 for robust reading
                    return pd.read_csv(BytesIO(file_content), encoding="latin1")
            elif filename.lower().endswith((".xlsx", ".xls")):
                return pd.read_excel(BytesIO(file_content))
            else:
                logger.warning(
                    f"Unsupported file type for fallback reading: {filename}"
                )
                return None
        except Exception as e:
            logger.error(
                f"Failed to read file content into DataFrame: {e}", exc_info=True
            )
            return None


# Global instance
enhanced_processor = EnhancedDataProcessor()
