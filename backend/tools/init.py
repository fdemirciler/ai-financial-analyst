from .data_cleaner import DataCleaner
from .metadata_analyzer import MetadataAnalyzer
from .variance_analyzer import VarianceAnalyzer
from .trend_analyzer import TrendAnalyzer


def get_all_tools():
    return {
        "data_cleaner": DataCleaner(),
        "metadata_analyzer": MetadataAnalyzer(),
        "variance_analyzer": VarianceAnalyzer(),
        "trend_analyzer": TrendAnalyzer(),
    }
