#!/usr/bin/env python3
"""Interactive, confirmation-gated user-space repair smoke test.

The command is intentionally conservative: it audits and prints a plan first.
Real downloads/installations require a validated official artifact supplied by
the environment workflow; this script never invents one.
"""
from pathlib import Path
import sys
import argparse

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from core.environment import (AdoptiumProvider, AndroidSDKDiscovery, LocalJDKDiscovery,
                              LocalSDKDiscovery, analyze_flutter_toolchain,
                              build_android_repair_plan, EnvironmentRepairWorkflow)
from core.environment.user_space_repair import preflight_user_space, jdk_artifact_from_research


def main(argv=None) -> int:
    parser = argparse.ArgumentParser(description="Préparation Flutter/Android user-space contrôlée")
    parser.add_argument('--dry-run', action='store_true')
    parser.add_argument('--component', choices=('jdk', 'android', 'all'), default='all')
    args = parser.parse_args(argv)
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
    plan = build_android_repair_plan(android) if args.component in ('android', 'all') else type('Plan', (), {'operations': ()})()
    existing_jdk = next((candidate for candidate in jdks if candidate.java and candidate.javac), None)
    artifact = None
    if args.component in ('jdk', 'all') and existing_jdk is None and (not java["javac"] or not java["java_home"]):
        print("Research: recherche officielle Eclipse Adoptium...")
        try:
            import requests
            research = AdoptiumProvider(fetcher=lambda url: requests.get(url, timeout=15).json()).research()
            artifact = jdk_artifact_from_research(research)
        except Exception as exc:
            print(f"Research: indisponible ({exc})")
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
    if artifact:
        print(f"JDK artifact: {artifact.version} / {artifact.source.url}")
        print(f"JDK checksum: {artifact.checksum}")
    elif "MISSING_JAVAC" in report.gaps:
        print("JDK artifact: aucune métadonnée officielle validée disponible")
    print("Planned Android actions:")
    if args.component in ('jdk', 'all') and ('MISSING_JAVAC' in report.gaps or 'MISSING_JAVA_HOME' in report.gaps):
        print("  JDK: INSTALL_JDK → CONFIGURE_JAVA_HOME → CONFIGURE_PATH → VERIFY_JAVA → VERIFY_JAVAC")
    for index, operation in enumerate(plan.operations, 1):
        print(f"  {index}. {operation.action} — {operation.reason}")
    if not plan.operations and not artifact and not report.gaps:
        print("Environment already ready; nothing to repair.")
        return 0
    destination = Path.home() / ".local/share/jarvis/environments/jdk"
    preflight = preflight_user_space(destination)
    print(f"Preflight: {'OK' if preflight.ok else 'FAILED'}")
    if not preflight.ok:
        print("Errors:", ", ".join(preflight.errors))
        return 2
    if args.dry_run:
        print("DRY-RUN: aucune modification effectuée.")
        return 0
    answer = input("Confirm user-space repair? [y/N] ").strip().lower()
    if answer not in {"y", "yes"}:
        print("CANCELLED: aucune modification effectuée.")
        return 0
    if artifact:
        reports = EnvironmentRepairWorkflow().execute(jdk_artifact=artifact,
            confirmation_handler=lambda _step: True, dry_run=False)
        success = bool(reports) and all(item.to_dict().get("success") for item in reports)
        print("REAL EXECUTION:", "SUCCESS" if success else "FAILED")
        return 0 if success else 4
    print("BLOCKED: aucune métadonnée officielle Temurin validée n'est disponible.")
    return 3


if __name__ == "__main__":
    raise SystemExit(main())
