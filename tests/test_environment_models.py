from core.environment.models import CheckStatus, EnvironmentCheck


def test_environment_check_is_structured():
    check = EnvironmentCheck("git", CheckStatus.PRESENT, version="2.0", path="/usr/bin/git")
    assert check.installed is True
    assert check.to_dict()["status"] == "PRESENT"


def test_unknown_is_not_absent():
    check = EnvironmentCheck("tool", CheckStatus.UNKNOWN, confidence=0.4)
    assert check.installed is False
    assert check.to_dict()["confidence"] == 0.4
