"""采集 Tools（适配器 + 注册表 + 合规联动）单测。"""

import pytest

from core.compliance import ComplianceError, ComplianceGateway
from core.models import SourceType
from core.tools.base import AdapterRegistry, RawDocument
from core.tools.web import RegulatorFetchAdapter, WebFetchAdapter


def _fake_fetch(url: str) -> str:
    return f"<html>content of {url}</html>"


def test_web_adapter_returns_rawdocument():
    a = WebFetchAdapter(raw_fetch=_fake_fetch)
    doc = a.fetch("https://example.com")
    assert isinstance(doc, RawDocument)
    assert doc.source_type is SourceType.WEB
    assert "example.com" in doc.content


def test_registry_register_and_fetch():
    reg = AdapterRegistry(gateway=ComplianceGateway())
    reg.register(WebFetchAdapter(raw_fetch=_fake_fetch))
    doc = reg.fetch(SourceType.WEB, "https://example.com")
    assert "example.com" in doc.content


def test_registry_unknown_source():
    reg = AdapterRegistry()
    with pytest.raises(KeyError):
        reg.get(SourceType.REGULATOR)


def test_registry_gateway_blocks_blacklisted():
    reg = AdapterRegistry(gateway=ComplianceGateway(blacklist_domains={"blocked.com"}))
    reg.register(WebFetchAdapter(raw_fetch=_fake_fetch))
    with pytest.raises(ComplianceError):
        reg.fetch(SourceType.WEB, "https://blocked.com/x")


def test_regulator_adapter_source_type():
    reg = AdapterRegistry()
    reg.register(RegulatorFetchAdapter(raw_fetch=_fake_fetch))
    doc = reg.fetch(SourceType.REGULATOR, "https://mas.gov.sg", legal_basis="public regulator")
    assert doc.source_type is SourceType.REGULATOR
    assert doc.legal_basis == "public regulator"
