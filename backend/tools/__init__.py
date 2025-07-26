from .base import AnalysisTool
from .data_cleaner import DataCleaner
from .metadata_analyzer import MetadataAnalyzer
from .trend_analyzer import TrendAnalyzer
from .variance_analyzer import VarianceAnalyzer


def get_all_tools() -> dict[str, AnalysisTool]:
    """
    Returns a dictionary of all available analysis tools.
    """
    return {
        "data_cleaner": DataCleaner(),
        "metadata_analyzer": MetadataAnalyzer(),
        "trend_analyzer": TrendAnalyzer(),
        "variance_analyzer": VarianceAnalyzer(),
    }
