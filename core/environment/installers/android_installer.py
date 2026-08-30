from .artifacts import InstallationPlan, InstallationStep

class AndroidInstaller:
    """Typed plans for one Android SDK component; no shell commands."""
    def plan_component(self, component: str = "cmdline-tools"):
        if component not in {"platform-tools", "build-tools", "platforms", "cmdline-tools"}:
            raise ValueError("Composant Android non autorisé.")
        return InstallationPlan(component, [
            InstallationStep(f"android-{component}-download", component, "DOWNLOAD", 1, []),
            InstallationStep(f"android-{component}-verify-file", component, "VERIFY", 2, [f"android-{component}-download"], requires_confirmation=False),
            InstallationStep(f"android-{component}-extract", component, "EXTRACT", 3, [f"android-{component}-verify-file"], requires_confirmation=False),
            InstallationStep(f"android-{component}-install", component, "INSTALL", 4, [f"android-{component}-extract"], requires_confirmation=False),
            InstallationStep(f"android-{component}-verify", component, "VERIFY_ANDROID_COMPONENT", 5, [f"android-{component}-install"], requires_confirmation=False),
        ])
