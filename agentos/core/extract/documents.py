"""文档解析：把 HTML/PDF 原文转为纯文本，供提取层使用。

- `DocumentParser` 协议：生产可接 Docling（PDF→结构化）。
- `BasicHtmlParser`：标准库实现，去标签/脚本，抽正文文本，离线可用可测。
- `get_parser()`：若安装 docling 则用之，否则回退 BasicHtmlParser。
"""

from __future__ import annotations

import re
from html.parser import HTMLParser
from typing import Protocol


class DocumentParser(Protocol):
    def to_text(self, content: str, content_type: str = "text/html") -> str: ...


class _TextExtractor(HTMLParser):
    def __init__(self) -> None:
        super().__init__()
        self._chunks: list[str] = []
        self._skip = False

    def handle_starttag(self, tag, attrs):
        if tag in {"script", "style", "noscript"}:
            self._skip = True

    def handle_endtag(self, tag):
        if tag in {"script", "style", "noscript"}:
            self._skip = False

    def handle_data(self, data):
        if not self._skip and data.strip():
            self._chunks.append(data.strip())

    def text(self) -> str:
        return re.sub(r"\s+", " ", " ".join(self._chunks)).strip()


class BasicHtmlParser:
    """标准库 HTML/纯文本解析。"""

    def to_text(self, content: str, content_type: str = "text/html") -> str:
        if "html" not in content_type and "<" not in content:
            return re.sub(r"\s+", " ", content).strip()
        p = _TextExtractor()
        p.feed(content)
        return p.text()


def get_parser() -> DocumentParser:
    """优先 Docling（若已安装），否则基础解析器。"""
    try:  # pragma: no cover - 取决于是否安装 docling
        import docling  # noqa: F401

        return _DoclingParser()
    except Exception:  # noqa: BLE001
        return BasicHtmlParser()


class _DoclingParser:  # pragma: no cover - 需安装 docling
    def to_text(self, content: str, content_type: str = "text/html") -> str:
        from docling.document_converter import DocumentConverter

        conv = DocumentConverter()
        result = conv.convert_string(content)  # 版本 API 可能不同，生产按 docling 文档调整
        return result.document.export_to_markdown()
