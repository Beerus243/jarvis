"""Controlled orchestration from validated artifacts to InstallationEngine."""
from __future__ import annotations
from dataclasses import dataclass, field
from .installation_engine import InstallationEngine, InstallationReport
from .installers.jdk_installer import JdkInstaller
from .installers.android_installer import AndroidInstaller
from .lock import InstallationLock

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
        with self.lock_factory():
            if jdk_artifact:
                reports.append(self.engine.execute(self.plan_jdk(), artifact=jdk_artifact,
                                                   dry_run=dry_run, confirmation_handler=confirmation_handler))
            if android_artifact:
                reports.append(self.engine.execute(self.plan_android(), artifact=android_artifact,
                                                   sdk_root=android_artifact.destination, dry_run=dry_run,
                                                   confirmation_handler=confirmation_handler))
        return reports
