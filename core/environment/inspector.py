from __future__ import annotations

from .commands import detect_command, detect_package_managers
from .detector import (COMMANDS, inspect_android, inspect_applications, inspect_flutter,
                       inspect_gpu, inspect_network, inspect_storage, inspect_system)


def inspect_environment() -> dict:
    commands = {name: detect_command(name).to_dict() for name in COMMANDS}
    return {
        "system": inspect_system(),
        "package_manager": detect_package_managers(),
        "commands": commands,
        "applications": inspect_applications(),
        "flutter": inspect_flutter(commands),
        "java": {"java": commands["java"], "javac": commands["javac"]},
        "android": inspect_android(),
        "environment": {key: value for key, value in __import__("os").environ.items()
                         if key in {"PATH", "JAVA_HOME", "ANDROID_HOME", "ANDROID_SDK_ROOT", "FLUTTER_ROOT"}},
        "gpu": inspect_gpu(),
        "network": inspect_network(),
        "storage": inspect_storage(),
    }


def format_environment_report(result: dict) -> str:
    system = result.get("system", {})
    lines = ["JARVIS — Analyse de l'environnement", "", "Système :"]
    lines.extend(f"    {key}: {system.get(key) or 'inconnu'}" for key in
                 ("distribution", "kernel", "architecture", "hostname", "user", "cwd"))
    lines.append("\nOutils :")
    for name, check in result.get("commands", {}).items():
        mark = "✓" if check.get("status") == "PRESENT" else "✗"
        lines.append(f"    {name:<10} {mark} {check.get('version') or ''}".rstrip())
    lines.append("\nApplications :")
    for name, check in result.get("applications", {}).items():
        lines.append(f"    {name:<10} {'✓' if check.get('status') == 'PRESENT' else '✗'}")
    android = result.get("android", {})
    lines.extend(["\nAndroid :", f"    SDK        {'✓' if android.get('android_sdk', {}).get('status') == 'PRESENT' else '✗'}",
                  f"    Studio     {'✓' if android.get('android_studio', {}).get('status') == 'PRESENT' else '✗'}"])
    lines.append("\nAucune installation ni modification n'est effectuée.")
    return "\n".join(lines)
