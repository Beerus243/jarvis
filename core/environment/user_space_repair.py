"""Safe user-space preparation helpers for JDK/Android repair.

This module builds and validates operations.  It never invokes a shell and it
never mutates the machine unless an explicit caller invokes the profile helper.
"""
from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path
import os
import shutil
import stat
import tempfile

from .installers.jdk_installer import JdkInstaller
from .installers.artifacts import InstallationArtifact
from .research import EnvironmentResearchResult
from .shell_profile import UserShellProfile
from .user_path import validate_user_path


@dataclass(frozen=True)
class PreflightResult:
    ok: bool
    checks: tuple[str, ...] = ()
    errors: tuple[str, ...] = ()


def preflight_user_space(destination: str | Path, *, architecture: str = "x86_64") -> PreflightResult:
    checks = []
    errors = []
    try:
        root = Path(destination).expanduser().resolve()
        home = Path.home().resolve()
        if root != home and home not in root.parents:
            raise ValueError("Le chemin doit rester dans le répertoire utilisateur.")
        checks.append("destination_user_space")
        parent = root
        while not parent.exists() and parent != parent.parent:
            parent = parent.parent
        if not parent.exists() or not (parent.stat().st_mode & stat.S_IWUSR):
            errors.append("destination_not_writable")
    except (OSError, ValueError) as exc:
        errors.append(str(exc))
    if architecture not in {"x86_64", "aarch64"}:
        errors.append("architecture_unsupported")
    else:
        checks.append("architecture_supported")
    if shutil.disk_usage(Path.home()).free < 512 * 1024 * 1024:
        errors.append("insufficient_disk_space")
    else:
        checks.append("disk_space_available")
    return PreflightResult(not errors, tuple(checks), tuple(errors))


def jdk_artifact_from_research(research: EnvironmentResearchResult, *, architecture: str = "x86_64") -> InstallationArtifact | None:
    """Convert only validated official Temurin metadata to an artifact."""
    if architecture != "x86_64":
        return None
    return JdkInstaller().artifact_from_research(research)


class UserEnvironmentConfigurator:
    """Idempotent, backup-able JAVA_HOME/PATH updates in user profiles."""

    def __init__(self, profile: str | Path | None = None, shell: str | None = None):
        self.profile = Path(profile).expanduser() if profile else UserShellProfile(shell=shell).path_file
        self.profile = self.profile.resolve()
        home = Path.home().resolve()
        if home not in self.profile.parents and self.profile != home:
            raise ValueError("Profil hors du répertoire utilisateur.")

    def _lines(self, java_home: Path, android_sdk: Path | None = None, flutter: Path | None = None):
        entries = [("JAVA_HOME", java_home), ("PATH", java_home / "bin")]
        if android_sdk:
            entries += [("ANDROID_HOME", android_sdk), ("ANDROID_SDK_ROOT", android_sdk),
                        ("PATH", android_sdk / "platform-tools"),
                        ("PATH", android_sdk / "cmdline-tools/latest/bin")]
        if flutter:
            entries.append(("PATH", flutter / "bin"))
        shell = self.profile.name
        fish = shell == "config.fish"
        lines = []
        for variable, value in entries:
            value = validate_user_path(value)
            if fish:
                lines.append(f'set -gx {variable} "{value}"') if variable != "PATH" else lines.append(f'set -gx PATH "{value}" $PATH')
            elif variable == "JAVA_HOME":
                lines.append(f'export JAVA_HOME="{value}"')
            elif variable == "PATH":
                lines.append(f'export PATH="{value}:$PATH"')
            else:
                lines.append(f'export {variable}="{value}"')
        return lines

    def plan(self, java_home: str | Path, *, android_sdk: str | Path | None = None, flutter: str | Path | None = None):
        return tuple(self._lines(Path(java_home).expanduser().resolve(), Path(android_sdk).expanduser().resolve() if android_sdk else None, Path(flutter).expanduser().resolve() if flutter else None))

    def apply(self, lines: tuple[str, ...], *, confirmed: bool = False) -> Path | None:
        if not confirmed:
            return None
        old = self.profile.read_text(encoding="utf-8") if self.profile.exists() else ""
        backup = Path(tempfile.mkstemp(prefix=f"{self.profile.name}.jarvis-", suffix=".bak", dir=self.profile.parent)[1])
        backup.write_text(old, encoding="utf-8")
        existing = set(old.splitlines())
        content = old.rstrip("\n")
        additions = [line for line in lines if line not in existing]
        if additions:
            content += ("\n" if content else "") + "\n".join(additions) + "\n"
            self.profile.parent.mkdir(parents=True, exist_ok=True)
            self.profile.write_text(content, encoding="utf-8")
        return backup

    def rollback(self, backup: str | Path):
        self.profile.write_text(Path(backup).read_text(encoding="utf-8"), encoding="utf-8")
