from __future__ import annotations

import os
import platform
import shutil
import socket
import subprocess
from pathlib import Path
from typing import Callable

from tools.applications import APPLICATIONS

from .commands import detect_command
from .models import CheckStatus, EnvironmentCheck


COMMANDS = ("git", "python", "node", "npm", "flutter", "dart", "java", "javac", "adb", "code")


def inspect_system() -> dict:
    info = platform.freedesktop_os_release() if hasattr(platform, "freedesktop_os_release") else {}
    return {
        "os": platform.system(),
        "distribution": info.get("NAME") or platform.system(),
        "distribution_version": info.get("VERSION_ID") or info.get("VERSION"),
        "kernel": platform.release(),
        "architecture": platform.machine(),
        "hostname": socket.gethostname(),
        "user": os.environ.get("USER") or os.environ.get("USERNAME"),
        "home": str(Path.home()),
        "cwd": str(Path.cwd()),
        "shell": os.environ.get("SHELL"),
    }


def inspect_applications(*, which: Callable[[str], str | None] = shutil.which) -> dict:
    result = {}
    for name, definition in APPLICATIONS.items():
        found = next((which(command[0]) for command in definition["commands"] if which(command[0])), None)
        result[name] = EnvironmentCheck(
            name=name,
            status=CheckStatus.PRESENT if found else CheckStatus.ABSENT,
            path=found,
            command=name,
            details={"label": definition["label"]},
        ).to_dict()
    return result


def inspect_flutter(commands: dict) -> dict:
    flutter = commands["flutter"]
    dart = commands["dart"]
    return {"flutter": flutter, "dart_version": dart.get("version") if dart["status"] == "PRESENT" else None}


def inspect_android(*, which: Callable[[str], str | None] = shutil.which) -> dict:
    roots = []
    for variable in ("ANDROID_HOME", "ANDROID_SDK_ROOT"):
        value = os.environ.get(variable)
        if value:
            roots.append(Path(value).expanduser())
    roots.extend([Path.home() / "Android/Sdk", Path.home() / "Android/sdk"])
    sdk = next((root for root in roots if root.is_dir()), None)
    adb = which("adb")
    if not adb and sdk:
        candidate = sdk / "platform-tools/adb"
        adb = str(candidate) if candidate.exists() else None
    return {
        "android_sdk": {
            "status": CheckStatus.PRESENT.value if sdk else CheckStatus.ABSENT.value,
            "path": str(sdk) if sdk else None,
            "adb": adb,
            "platforms": str(sdk / "platforms") if sdk and (sdk / "platforms").is_dir() else None,
            "build_tools": str(sdk / "build-tools") if sdk and (sdk / "build-tools").is_dir() else None,
        },
        "android_studio": _detect_android_studio(which),
    }


def _detect_android_studio(which: Callable[[str], str | None]) -> dict:
    path = which("studio") or which("android-studio")
    candidates = [Path.home() / ".local/share/JetBrains/Toolbox/apps/AndroidStudio",
                  Path("/opt/android-studio")]
    if not path:
        path = next((str(item) for item in candidates if item.exists()), None)
    return EnvironmentCheck("android_studio", CheckStatus.PRESENT if path else CheckStatus.ABSENT,
                            path=path, command="android-studio").to_dict()


def inspect_gpu(*, which: Callable[[str], str | None] = shutil.which,
                runner: Callable[..., subprocess.CompletedProcess] = subprocess.run) -> dict:
    nvidia = which("nvidia-smi")
    if not nvidia:
        return {"status": CheckStatus.UNKNOWN.value, "vendor": None, "device": None, "driver": None}
    try:
        result = runner([nvidia, "--query-gpu=name,driver_version", "--format=csv,noheader"],
                        capture_output=True, text=True, timeout=3, check=False)
        if result.returncode == 0 and result.stdout.strip():
            device, _, driver = result.stdout.strip().partition(",")
            return {"status": CheckStatus.PRESENT.value, "vendor": "NVIDIA",
                    "device": device.strip(), "driver": driver.strip() or None}
    except (OSError, subprocess.SubprocessError, TimeoutError):
        pass
    return {"status": CheckStatus.UNKNOWN.value, "vendor": "NVIDIA", "device": None, "driver": None}


def inspect_network() -> dict:
    try:
        with socket.create_connection(("1.1.1.1", 53), timeout=0.5):
            return {"network_available": True}
    except OSError:
        return {"network_available": False}


def inspect_storage() -> dict:
    usage = shutil.disk_usage(Path.home())
    return {"home_disk_total": usage.total, "home_disk_free": usage.free}
