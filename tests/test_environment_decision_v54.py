from core.environment.capabilities import EnvironmentCapabilities
from core.environment.decision import decide, format_decision

def test_build_blocked_with_missing_javac():
    d=decide(EnvironmentCapabilities(java_runtime=True))
    assert d.status == "BLOCKED" and "javac" in d.missing[0]

def test_build_ready_message():
    d=decide(EnvironmentCapabilities(javac=True, java_home=True, sdkmanager=True))
    assert "prêt" in format_decision(d).lower()
