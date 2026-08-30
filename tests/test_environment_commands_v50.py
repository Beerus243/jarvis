from core.environment.intent import detect_environment_intent
from core.environment.capabilities import EnvironmentCapabilities, check_environment

def test_environment_audit_intent():
    assert detect_environment_intent("vérifie mon environnement").intent == "ENVIRONMENT_AUDIT"

def test_flutter_android_build_intent():
    intent = detect_environment_intent("suis-je prêt pour compiler Flutter Android")
    assert intent.intent == "FLUTTER_ANDROID_BUILD_CHECK" and intent.capability == "flutter_android_build"

def test_environment_gaps_intent():
    assert detect_environment_intent("qu'est-ce qui manque ?").intent == "ENVIRONMENT_GAPS"

def test_capability_check_is_local_and_structured():
    result = check_environment("jdk", capabilities=EnvironmentCapabilities(java_runtime=True), provider_state="NETWORK_UNAVAILABLE")
    assert result["status"] == "BLOCKED_NETWORK" and "javac" in result["missing"]
