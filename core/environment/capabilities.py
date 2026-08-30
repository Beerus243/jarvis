"""Capability-level readiness built on the existing environment discoveries."""
from __future__ import annotations
from dataclasses import dataclass, asdict
import shutil
from .local_sdks import LocalSDKDiscovery
from .local_jdks import LocalJDKDiscovery
from .android_sdk import AndroidSDKDiscovery

@dataclass(frozen=True)
class EnvironmentCapabilities:
    flutter: bool = False
    dart: bool = False
    java_runtime: bool = False
    javac: bool = False
    java_home: bool = False
    android_sdk: bool = False
    adb: bool = False
    build_tools: bool = False
    platforms: bool = False
    sdkmanager: bool = False
    android_licenses: bool = False

    def to_dict(self):
        return asdict(self)

def discover_capabilities():
    sdk = next(iter(LocalSDKDiscovery().discover()), None)
    android = AndroidSDKDiscovery().discover()
    jdks = LocalJDKDiscovery().discover()
    java_runtime = bool(shutil.which("java")) or any(item.java for item in jdks)
    javac = bool(shutil.which("javac")) or any(item.javac for item in jdks)
    return EnvironmentCapabilities(
        flutter=bool(sdk and sdk.flutter), dart=bool(sdk and sdk.dart),
        java_runtime=java_runtime, javac=javac,
        java_home=bool(__import__("os").environ.get("JAVA_HOME")),
        android_sdk=android.sdk == "PRESENT", adb=android.adb != "MISSING",
        build_tools=android.build_tools != "MISSING", platforms=android.platforms != "MISSING",
        sdkmanager=android.cmdline_tools != "MISSING", android_licenses=android.licenses == "ACCEPTED")

def check_environment(capability="flutter_android_build", *, capabilities=None, provider_state="NETWORK_UNAVAILABLE"):
    caps = capabilities or discover_capabilities()
    requirements = {
        "flutter": ("flutter", "dart"),
        "android": ("android_sdk", "adb", "build_tools", "platforms"),
        "jdk": ("java_runtime", "javac"),
        "android_package_management": ("android_sdk", "sdkmanager"),
        "flutter_android_build": ("flutter", "dart", "android_sdk", "adb", "build_tools", "platforms", "java_runtime", "javac"),
    }
    if capability not in requirements:
        raise ValueError(f"Capacité inconnue: {capability}")
    required = requirements[capability]
    satisfied = tuple(name for name in required if getattr(caps, name))
    missing = tuple(name for name in required if not getattr(caps, name))
    if not missing:
        status = "READY"
    elif provider_state == "NETWORK_UNAVAILABLE":
        status = "BLOCKED_NETWORK"
    else:
        status = "PARTIAL"
    return {"capability": capability, "status": status, "satisfied": satisfied,
            "missing": missing, "capabilities": caps.to_dict(),
            "repairability": "BLOCKED_NETWORK" if status == "BLOCKED_NETWORK" else "AVAILABLE"}

def format_capability_report(result):
    lines = [f"Capacité : {result['capability']}", f"État : {result['status']}", "", "Satisfait :"]
    lines.extend(f"- {item}" for item in result["satisfied"])
    lines.append("Manquant :")
    lines.extend(f"- {item}" for item in result["missing"])
    lines.append(f"Réparabilité : {result['repairability']}")
    return "\n".join(lines)
