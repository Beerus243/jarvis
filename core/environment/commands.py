from __future__ import annotations

import re
import shutil
import subprocess
from typing import Callable

from .models import CheckStatus, EnvironmentCheck


def _clean_version(output: str) -> str | None:
    text = " ".join(str(output or "").split())
    return text or None


def detect_command(
    name: str,
    *,
    which: Callable[[str], str | None] = shutil.which,
    runner: Callable[..., subprocess.CompletedProcess] = subprocess.run,
) -> EnvironmentCheck:
    """Detect one executable without raising when it is absent or unusable."""
    path = which(name)
    if not path:
        return EnvironmentCheck(name=name, status=CheckStatus.ABSENT,
                                command=name, confidence=1.0)
    try:
        result = runner([path, "--version"], capture_output=True, text=True,
                        timeout=3, check=False)
        output = (result.stdout or result.stderr or "").strip()
        status = CheckStatus.PRESENT if result.returncode == 0 else CheckStatus.UNKNOWN
        return EnvironmentCheck(name=name, status=status, version=_clean_version(output),
                                path=path, command=name,
                                details={"returncode": result.returncode},
                                confidence=1.0 if status == CheckStatus.PRESENT else 0.6)
    except (OSError, subprocess.SubprocessError, TimeoutError) as error:
        return EnvironmentCheck(name=name, status=CheckStatus.UNKNOWN, path=path,
                                command=name, details={"error": str(error)}, confidence=0.5)


def detect_package_managers(*, which: Callable[[str], str | None] = shutil.which,
                            runner: Callable[..., subprocess.CompletedProcess] = subprocess.run) -> dict:
    managers = [detect_command(name, which=which, runner=runner)
                for name in ("dnf", "apt", "pacman", "zypper", "apk", "brew")]
    selected = next((item for item in managers if item.status == CheckStatus.PRESENT), None)
    return {
        "selected": selected.to_dict() if selected else None,
        "available": [item.to_dict() for item in managers],
    }
