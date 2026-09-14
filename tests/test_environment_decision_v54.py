from core.environment.capabilities import EnvironmentCapabilities
from core.environment.decision import decide, format_decision

def test_build_blocked_with_missing_javac():
    d=decide(EnvironmentCapabilities(java_runtime=True), network_available=False)
    assert d.status == "BLOCKED" and "javac" in d.missing[0]

def test_build_ready_message():
    d=decide(EnvironmentCapabilities(**{name: True for name in EnvironmentCapabilities.__dataclass_fields__}))
    assert "prêt" in format_decision(d).lower()
