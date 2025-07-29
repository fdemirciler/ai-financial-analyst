"""Pipeline package initialization.
Defines global constants and makes key classes available at package level."""

from importlib.metadata import version as _get_version

PIPELINE_VERSION: str = "0.1.0"

# Expose commonly used objects once they are implemented
try:
    from .pipeline import Pipeline  # noqa: F401, E402  # pylint: disable=unused-import
except ImportError:  # circular during initial scaffolding
    Pipeline = None  # type: ignore

__all__ = [
    "PIPELINE_VERSION",
    "Pipeline",
]
