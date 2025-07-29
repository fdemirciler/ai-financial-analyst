"""Enhanced tools that leverage the new pipeline while maintaining compatibility.

These tools serve as adapters between the legacy tool interface and the new
pipeline architecture, providing enhanced capabilities while maintaining
backward compatibility.
"""

from typing import Dict, Any
import pandas as pd
from pipeline.schemas import PipelineConfig, CleanerConfig, ProfilerConfig
from pipeline.type_inferencer import TypeInferencer
from pipeline.profiler import profile_dataframe
from pipeline.audit import AuditLogger
from .base import AnalysisTool


class EnhancedDataCleaner(AnalysisTool):
    """Enhanced data cleaner using the new pipeline type inference and cleaning logic."""

    @property
    def name(self) -> str:
        return "enhanced_data_cleaner"

    @property
    def description(self) -> str:
        return "Cleans and standardizes data using advanced type inference and configurable strategies"

    async def execute(
        self, data: pd.DataFrame, parameters: Dict[str, Any]
    ) -> Dict[str, Any]:
        try:
            # Get exclude columns from parameters (from enhanced preprocessor)
            exclude_columns = parameters.get("exclude_columns", [])

            # Create a copy of the data for cleaning
            cleaned_data = data.copy()

            # Get type information for intelligent cleaning
            type_info = TypeInferencer.infer(data)

            # Standardize column names and update exclude_columns list accordingly
            standardized_exclude = []
            new_columns = {}
            for col in cleaned_data.columns:
                new_col_name = str(col).lower().replace(" ", "_")
                new_columns[col] = new_col_name
                if col in exclude_columns:
                    standardized_exclude.append(new_col_name)

            cleaned_data.rename(columns=new_columns, inplace=True)

            # Process each column based on its inferred type
            for original_col, col_info in type_info.items():
                # Get the standardized column name
                col = new_columns.get(
                    original_col, str(original_col).lower().replace(" ", "_")
                )

                if col in standardized_exclude:
                    continue

                if col not in cleaned_data.columns:
                    continue

                column_type = col_info.get("column_type", "text")

                try:
                    if column_type == "currency":
                        # Clean currency columns
                        cleaned_data[col] = self._clean_currency(cleaned_data[col])
                    elif column_type == "percentage":
                        # Clean percentage columns
                        cleaned_data[col] = self._clean_percentage(cleaned_data[col])
                    elif column_type == "period":
                        # Period columns should remain as strings/text
                        cleaned_data[col] = cleaned_data[col].astype(str)
                    elif column_type == "numeric":
                        # Convert to numeric
                        cleaned_data[col] = pd.to_numeric(
                            cleaned_data[col], errors="coerce"
                        )
                    elif column_type == "date":
                        # Convert to datetime
                        cleaned_data[col] = pd.to_datetime(
                            cleaned_data[col], errors="coerce"
                        )
                    # For id and text types, leave as is

                except Exception as e:
                    # If cleaning fails for a specific column, log but continue
                    print(
                        f"Warning: Failed to clean column {col} as {column_type}: {e}"
                    )
                    continue

            # Handle missing values
            for col in cleaned_data.columns:
                if col not in standardized_exclude:
                    if cleaned_data[col].dtype in ["float64", "int64"]:
                        # Use median for numeric columns
                        cleaned_data[col] = cleaned_data[col].fillna(
                            cleaned_data[col].median()
                        )
                    elif cleaned_data[col].dtype == "object":
                        # Fill text columns with empty string
                        cleaned_data[col] = cleaned_data[col].fillna("")

            # Remove rows and columns that are completely empty
            cleaned_data.dropna(how="all", inplace=True)
            cleaned_data.dropna(axis=1, how="all", inplace=True)

            # Ensure JSON-serializable output
            json_output = []
            for _, row in cleaned_data.iterrows():
                record = {}
                for col, value in row.items():
                    if pd.isna(value):
                        record[col] = None
                    elif isinstance(value, pd.Timestamp):
                        record[col] = value.isoformat()
                    elif isinstance(value, pd.DatetimeIndex):
                        record[col] = str(value)
                    else:
                        record[col] = value
                json_output.append(record)

            dtypes = cleaned_data.dtypes.astype(str).to_dict()

            return {
                "success": True,
                "data": json_output,
                "dtypes": dtypes,
                "shape": cleaned_data.shape,
                "columns": list(cleaned_data.columns),
                "message": f"Data cleaned successfully using enhanced pipeline. Shape: {cleaned_data.shape}",
                "type_inference_used": True,
                "types_detected": {
                    col: info.get("column_type") for col, info in type_info.items()
                },
            }

        except Exception as e:
            import traceback

            traceback.print_exc()
            return {
                "success": False,
                "error": str(e),
                "message": f"Enhanced cleaning failed: {str(e)}",
            }

    def _clean_currency(self, series: pd.Series) -> pd.Series:
        """Clean currency values by removing symbols and converting to numeric."""
        try:
            # Convert to string and remove currency symbols and commas
            cleaned = (
                series.astype(str)
                .str.replace(r"[\$€£¥₹]", "", regex=True)
                .str.replace(",", "")
                .str.strip()
            )
            return pd.to_numeric(cleaned, errors="coerce")
        except Exception:
            return series

    def _clean_percentage(self, series: pd.Series) -> pd.Series:
        """Clean percentage values by removing % and converting to decimal."""
        try:
            cleaned = series.astype(str).str.replace("%", "").str.replace(",", "")
            numeric = pd.to_numeric(cleaned, errors="coerce")
            return numeric / 100.0  # Convert to decimal
        except Exception:
            return series


class EnhancedDataProfiler(AnalysisTool):
    """Enhanced data profiler using the new pipeline profiling capabilities."""

    @property
    def name(self) -> str:
        return "enhanced_data_profiler"

    @property
    def description(self) -> str:
        return "Creates comprehensive data profiles with advanced statistical analysis and data quality assessment"

    async def execute(
        self, data: pd.DataFrame, parameters: Dict[str, Any]
    ) -> Dict[str, Any]:
        try:
            # Create configuration
            config = PipelineConfig()
            config.profiler.mode = parameters.get("profiler_mode", "builtin")
            config.profiler.correlation = parameters.get("include_correlation", True)

            # Create audit logger
            audit = AuditLogger()

            # Generate profile using the new pipeline
            profile = profile_dataframe(data, config, audit)

            # Convert ProfileJSON to legacy format for compatibility
            legacy_profile = {
                "basic_stats": profile.basic_stats,
                "periods": profile.periods,
                "metrics": profile.metrics,
                "columns": profile.columns,
                "sample_data": profile.sample_data,
            }

            return {
                "success": True,
                "profile": legacy_profile,
                "message": f"Enhanced data profile created successfully. Advanced analysis completed.",
                "audit_trail": audit.to_trail().model_dump(),
                "profiler_mode": config.profiler.mode,
                "correlation_analysis": config.profiler.correlation,
            }

        except Exception as e:
            import traceback

            traceback.print_exc()

            # Fallback to basic profiling if enhanced profiler fails
            try:
                basic_stats = {}
                for col in data.columns:
                    if data[col].dtype in ["int64", "float64"]:
                        basic_stats[col] = {
                            "mean": (
                                float(data[col].mean())
                                if not data[col].isna().all()
                                else None
                            ),
                            "std": (
                                float(data[col].std())
                                if not data[col].isna().all()
                                else None
                            ),
                            "min": (
                                float(data[col].min())
                                if not data[col].isna().all()
                                else None
                            ),
                            "max": (
                                float(data[col].max())
                                if not data[col].isna().all()
                                else None
                            ),
                            "count": int(data[col].count()),
                        }
                    else:
                        basic_stats[col] = {
                            "unique": int(data[col].nunique()),
                            "count": int(data[col].count()),
                            "most_frequent": (
                                str(data[col].mode().iloc[0])
                                if not data[col].empty and not data[col].mode().empty
                                else None
                            ),
                        }

                sample_data = data.head(3).to_dict("records")

                fallback_profile = {
                    "basic_stats": basic_stats,
                    "periods": [],
                    "metrics": [],
                    "columns": list(data.columns),
                    "sample_data": sample_data,
                }

                return {
                    "success": True,
                    "profile": fallback_profile,
                    "message": f"Data profile created using fallback method. Enhanced profiling failed: {str(e)}",
                    "profiler_mode": "fallback",
                    "correlation_analysis": False,
                }

            except Exception as fallback_error:
                return {
                    "success": False,
                    "error": str(e),
                    "fallback_error": str(fallback_error),
                    "message": f"Enhanced profiling failed: {str(e)}",
                }
            return {
                "success": False,
                "error": str(e),
                "message": f"Enhanced profiling failed: {str(e)}",
            }


class EnhancedDataPreprocessor(AnalysisTool):
    """Enhanced preprocessor using advanced type inference."""

    @property
    def name(self) -> str:
        return "enhanced_data_preprocessor"

    @property
    def description(self) -> str:
        return "Advanced data preprocessing with semantic type inference and confidence scoring"

    async def execute(
        self, data: pd.DataFrame, parameters: Dict[str, Any]
    ) -> Dict[str, Any]:
        try:
            # Use the new type inferencer
            type_info = TypeInferencer.infer(data)

            # Identify columns to exclude based on type inference
            exclude_columns = []
            type_summary = {}
            confidence_summary = {}

            for col, info in type_info.items():
                column_type = info["column_type"]
                confidence = info["confidence"]

                type_summary[col] = column_type
                # Ensure confidence is a float
                confidence_value = (
                    float(confidence) if isinstance(confidence, (int, float)) else 0.5
                )
                confidence_summary[col] = confidence_value

                # More sophisticated exclusion logic
                if column_type in ["id", "text"] and confidence_value > 0.7:
                    exclude_columns.append(col)
                elif column_type == "date" and parameters.get("exclude_dates", False):
                    exclude_columns.append(col)
                elif column_type == "period":
                    # Period columns (years) should NOT be excluded - they're data columns
                    pass
                elif confidence_value < parameters.get("min_confidence", 0.5):
                    exclude_columns.append(col)

            return {
                "success": True,
                "exclude_columns": exclude_columns,
                "type_info": type_info,
                "type_summary": type_summary,
                "confidence_summary": confidence_summary,
                "message": f"Enhanced preprocessing complete. Identified {len(exclude_columns)} columns to exclude with confidence-based logic.",
                "enhanced_features": {
                    "semantic_types": list(set(type_summary.values())),
                    "average_confidence": (
                        sum(confidence_summary.values()) / len(confidence_summary)
                        if confidence_summary
                        else 0
                    ),
                    "high_confidence_columns": [
                        col
                        for col, conf in confidence_summary.items()
                        if isinstance(conf, (int, float)) and conf > 0.8
                    ],
                },
            }

        except Exception as e:
            return {
                "success": False,
                "error": str(e),
                "message": f"Enhanced preprocessing failed: {str(e)}",
            }
