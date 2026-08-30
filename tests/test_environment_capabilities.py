from core.environment.capabilities import EnvironmentCapabilities, check_environment, format_capability_report

def test_flutter_android_build_reports_missing_javac():
    caps = EnvironmentCapabilities(flutter=True, dart=True, android_sdk=True, adb=True, build_tools=True, platforms=True, java_runtime=True)
    result = check_environment(capabilities=caps, provider_state="NETWORK_UNAVAILABLE")
    assert result["status"] == "BLOCKED_NETWORK" and result["missing"] == ("javac",)

def test_jdk_capability_ready():
    caps = EnvironmentCapabilities(java_runtime=True, javac=True)
    assert check_environment("jdk", capabilities=caps)["status"] == "READY"

def test_android_package_management_is_partial_when_sdkmanager_missing():
    caps = EnvironmentCapabilities(android_sdk=True)
    result = check_environment("android_package_management", capabilities=caps, provider_state="AVAILABLE")
    assert result["status"] == "PARTIAL" and result["missing"] == ("sdkmanager",)

def test_capability_report_is_human_readable():
    result = check_environment("flutter", capabilities=EnvironmentCapabilities(flutter=True, dart=True))
    assert "Capacité : flutter" in format_capability_report(result)
