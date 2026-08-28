"""合规网关单测。"""

from datetime import UTC

import pytest

from core.compliance import (
    ComplianceError,
    ComplianceGateway,
    flag_enabled,
    level_for,
    pii_expiry,
)
from core.models import ComplianceLevel, SourceType


def test_level_mapping():
    assert level_for(SourceType.WEB) is ComplianceLevel.GREEN
    assert level_for(SourceType.REGULATOR) is ComplianceLevel.GREEN
    assert level_for(SourceType.SOCIAL) is ComplianceLevel.YELLOW
    assert level_for(SourceType.GROUP) is ComplianceLevel.RED
    assert level_for(SourceType.LINKEDIN) is ComplianceLevel.RED


def test_green_passes():
    gw = ComplianceGateway()
    assert gw.check(SourceType.WEB, url="https://example.com") is ComplianceLevel.GREEN


def test_yellow_requires_legal_basis():
    gw = ComplianceGateway(require_legal_basis=True)
    with pytest.raises(ComplianceError):
        gw.check(SourceType.SOCIAL, url="https://twitter.com/x")
    # 提供 legal_basis 后放行
    assert gw.check(SourceType.SOCIAL, legal_basis="public post") is ComplianceLevel.YELLOW


def test_red_blocked_without_flag(monkeypatch):
    monkeypatch.delenv("ENABLE_M2_GROUP_MONITOR", raising=False)
    gw = ComplianceGateway()
    with pytest.raises(ComplianceError):
        gw.check(SourceType.GROUP, feature="M2_GROUP_MONITOR")


def test_red_allowed_with_flag(monkeypatch):
    monkeypatch.setenv("ENABLE_M2_GROUP_MONITOR", "true")
    gw = ComplianceGateway()
    assert gw.check(SourceType.GROUP, feature="M2_GROUP_MONITOR") is ComplianceLevel.RED


def test_flag_enabled(monkeypatch):
    monkeypatch.setenv("ENABLE_M6_AUTOSEND", "1")
    assert flag_enabled("M6_AUTOSEND") is True
    monkeypatch.setenv("ENABLE_M6_AUTOSEND", "false")
    assert flag_enabled("M6_AUTOSEND") is False
    assert flag_enabled("UNKNOWN") is False


def test_blacklist(monkeypatch):
    gw = ComplianceGateway(blacklist_domains={"blocked.com"})
    with pytest.raises(ComplianceError):
        gw.check(SourceType.WEB, url="https://blocked.com/page")


def test_pii_expiry_future():
    from datetime import datetime

    assert pii_expiry(30) > datetime.now(UTC)
