#!/usr/bin/env python3
"""Interactive, confirmation-gated user-space repair smoke test.

The command is intentionally conservative: it audits and prints a plan first.
Real downloads/installations require a validated official artifact supplied by
the environment workflow; this script never invents one.
"""
from pathlib import Path
import sys

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from core.environment import (AndroidSDKDiscovery, LocalJDKDiscovery,
                              LocalSDKDiscovery, analyze_flutter_toolchain,
                              build_android_repair_plan)
from core.environment.user_space_repair import preflight_user_space


def main() -> int:
    sdk = next(iter(LocalSDKDiscovery().discover()), None)
    android = AndroidSDKDiscovery().discover()
    jdks = LocalJDKDiscovery().discover()
    java = {
        "java": bool(jdks) or bool(__import__("shutil").which("java")),
        "javac": bool(__import__("shutil").which("javac")),
        "java_home": bool(__import__("os").environ.get("JAVA_HOME")),
    }
    if sdk is None:
        print("Flutter: MISSING")
        return 1
    report = analyze_flutter_toolchain(sdk, java=java, android=android)
    plan = build_android_repair_plan(android)
    print("JARVIS ENVIRONMENT REPAIR")
    print(f"Flutter: {'READY' if sdk.flutter else 'MISSING'}")
    print(f"Dart: {'READY' if sdk.dart else 'MISSING'}")
    print(f"Java runtime: {'PRESENT' if java['java'] else 'MISSING'}")
    print(f"JDK/javac: {'READY' if java['javac'] else 'MISSING'}")
    print(f"Android SDK: {android.root or 'MISSING'}")
    print(f"ADB: {android.adb} ({'PATH OK' if android.adb_in_path else 'PATH NOT CONFIGURED'})")
    print(f"Build tools: {android.build_tools}")
    print(f"Platforms: {android.platforms}")
    print(f"Command-line tools: {android.cmdline_tools}")
    print(f"Licenses: {android.licenses}")
    print(f"Gaps: {', '.join(report.gaps) or 'NONE'}")
    print("Planned Android actions:")
    for index, operation in enumerate(plan.operations, 1):
        print(f"  {index}. {operation.action} — {operation.reason}")
    if not plan.operations:
        print("Environment already ready; nothing to repair.")
        return 0
    destination = Path.home() / ".local/share/jarvis/environments/jdk"
    preflight = preflight_user_space(destination)
    print(f"Preflight: {'OK' if preflight.ok else 'FAILED'}")
    if not preflight.ok:
        print("Errors:", ", ".join(preflight.errors))
        return 2
    answer = input("Confirm user-space repair? [y/N] ").strip().lower()
    if answer not in {"y", "yes"}:
        print("CANCELLED: aucune modification effectuée.")
        return 0
    print("BLOCKED: aucune métadonnée officielle (version/URL/checksum) validée n'est disponible.")
    print("Recherchez et validez un artefact Temurin/Android via le workflow avant exécution.")
    return 3


if __name__ == "__main__":
    raise SystemExit(main())
