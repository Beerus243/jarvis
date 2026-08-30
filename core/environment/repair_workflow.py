"""Controlled orchestration from validated artifacts to InstallationEngine."""
from __future__ import annotations
from dataclasses import dataclass, field
from .installation_engine import InstallationEngine, InstallationReport
from .installers.jdk_installer import JdkInstaller
from .installers.android_installer import AndroidInstaller
from .lock import InstallationLock
from pathlib import Path
import shutil

@dataclass
class EnvironmentRepairWorkflow:
    engine: InstallationEngine = field(default_factory=InstallationEngine)
    lock_factory: object = InstallationLock

    def plan_jdk(self): return JdkInstaller().plan_installation()
    def plan_android(self, component='cmdline-tools'): return AndroidInstaller().plan_component(component)

    def execute(self, *, jdk_artifact=None, android_artifact=None, confirmation_handler=None, dry_run=True):
        """Execute only supplied validated artifacts; absent artifacts are blocked.

        The lock covers the complete transaction and is released on every exit.
        """
        if not dry_run and not (jdk_artifact or android_artifact):
            return []
        reports = []
        created = []
        with self.lock_factory():
            if jdk_artifact:
                destination = Path(jdk_artifact.destination).expanduser().resolve()
                existed = destination.exists()
                report = self.engine.execute(self.plan_jdk(), artifact=jdk_artifact,
                                             dry_run=dry_run, confirmation_handler=confirmation_handler)
                reports.append(report)
                if not existed and destination.exists():
                    created.append(destination)
            if android_artifact:
                reports.append(self.engine.execute(self.plan_android(), artifact=android_artifact,
                                                   sdk_root=android_artifact.destination, dry_run=dry_run,
                                                   confirmation_handler=confirmation_handler))
        if not dry_run and any(not report.to_dict().get('success') for report in reports):
            for path in created:
                if path.exists() and path.is_dir():
                    shutil.rmtree(path, ignore_errors=True)
        return reports
