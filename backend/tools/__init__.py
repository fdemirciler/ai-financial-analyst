from .base import AnalysisTool
from .data_cleaner import DataCleaner
from .data_profiler import DataProfiler
from .trend_analyzer import TrendAnalyzer
from .variance_analyzer import VarianceAnalyzer
from .preprocessor import DataPreprocessor
from .enhanced_tools import (
    EnhancedDataCleaner,
    EnhancedDataProfiler,
    EnhancedDataPreprocessor,
)


def get_all_tools() -> dict[str, AnalysisTool]:
    """
    Returns a dictionary of all available analysis tools.
    Enhanced tools are prioritized over legacy tools.
    """
    return {
        # Enhanced tools (prioritized)
        "data_preprocessor": EnhancedDataPreprocessor(),
        "data_cleaner": EnhancedDataCleaner(),
        "data_profiler": EnhancedDataProfiler(),
        # Analysis tools (unchanged)
        "trend_analyzer": TrendAnalyzer(),
        "variance_analyzer": VarianceAnalyzer(),
        # Legacy tools (available as fallback)
        "legacy_data_preprocessor": DataPreprocessor(),
        "legacy_data_cleaner": DataCleaner(),
        "legacy_data_profiler": DataProfiler(),
    }
