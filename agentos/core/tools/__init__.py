"""采集 Tools 包导出。"""

from core.tools.base import AdapterRegistry, FetchAdapter, RawDocument
from core.tools.web import RegulatorFetchAdapter, WebFetchAdapter

__all__ = [
    "AdapterRegistry",
    "FetchAdapter",
    "RawDocument",
    "WebFetchAdapter",
    "RegulatorFetchAdapter",
]
