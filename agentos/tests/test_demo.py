"""P1 端到端演示 smoke 测试。"""

from modules.demo import run_demo


def test_demo_runs_offline():
    result = run_demo(live=False)
    assert "profile" in result and "admission" in result
    # ③ 产出画像与业务聚焦
    assert result["profile"]["module"] == "M3"
    assert result["profile"]["verdict"]["business_focus"]
    # 串联后 ⑤ 产出新加坡准入清单
    assert result["admission"]["module"] == "M5"
    assert result["admission"]["verdict"]["country"] == "Singapore"
    assert result["admission"]["verdict"]["licenses"]
    # 每条 Insight 都有证据
    assert result["profile"]["evidence"] and result["admission"]["evidence"]
