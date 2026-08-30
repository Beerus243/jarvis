from dataclasses import dataclass
from .repair_engine import RepairOperation

@dataclass(frozen=True)
class AndroidRepairPlan:
    gaps: tuple[str,...]; operations: tuple[RepairOperation,...]; state: str
    def to_dict(self):
        return {
            'gaps': list(self.gaps),
            'operations': [o.__dict__ for o in self.operations],
            'state': self.state,
        }

def build_android_repair_plan(status, *, java_home=None):
    """Build a typed, non-executing plan from an Android SDK audit.

    ``java_home`` is accepted for callers that already collect JDK context; JDK
    repair remains owned by :class:`JdkInstaller` and is intentionally not
    duplicated here.
    """
    del java_home
    gaps = []
    operations = []
    if status.sdk != 'PRESENT':
        gaps.append('MISSING_ANDROID_SDK')
    if status.adb == 'MISSING':
        gaps.append('MISSING_ADB')
    elif not getattr(status, 'adb_in_path', True):
        gaps.append('MISSING_ANDROID_PATH')
    if status.build_tools == 'MISSING':
        gaps.append('MISSING_ANDROID_BUILD_TOOLS')
    if status.platforms == 'MISSING':
        gaps.append('MISSING_ANDROID_PLATFORM')
    if status.cmdline_tools == 'MISSING':
        gaps.append('MISSING_ANDROID_CMDLINE_TOOLS')
    elif not getattr(status, 'sdkmanager_in_path', True):
        gaps.append('MISSING_ANDROID_CMDLINE_PATH')
    if status.licenses != 'ACCEPTED':
        gaps.append('LICENSE_STATE_UNKNOWN')

    mapping = {
        'MISSING_ANDROID_SDK': ('CONFIGURE_ANDROID_SDK', 'SDK Android absent', 'VERIFY_ANDROID_SDK'),
        'MISSING_ANDROID_PATH': ('CONFIGURE_ANDROID_PATH', 'ADB détecté mais absent du PATH', 'VERIFY_ADB'),
        'MISSING_ADB': ('INSTALL_ANDROID_PLATFORM_TOOLS', 'ADB absent', 'VERIFY_ADB'),
        'MISSING_ANDROID_BUILD_TOOLS': ('INSTALL_ANDROID_BUILD_TOOLS', 'Build-tools absents', 'VERIFY_BUILD_TOOLS'),
        'MISSING_ANDROID_PLATFORM': ('INSTALL_ANDROID_PLATFORM', 'Platform Android absente', 'VERIFY_ANDROID_PLATFORM'),
        'MISSING_ANDROID_CMDLINE_TOOLS': ('INSTALL_ANDROID_CMDLINE_TOOLS', 'Command-line tools absents', 'VERIFY_CMDLINE_TOOLS'),
        'MISSING_ANDROID_CMDLINE_PATH': ('CONFIGURE_ANDROID_PATH', 'sdkmanager détecté mais absent du PATH', 'VERIFY_CMDLINE_TOOLS'),
        'LICENSE_STATE_UNKNOWN': ('ACCEPT_ANDROID_LICENSES', 'Licences Android non confirmées', 'VERIFY_FLUTTER_ANDROID_TOOLCHAIN'),
    }
    for gap in gaps:
        action, reason, verification = mapping[gap]
        operations.append(RepairOperation(action, reason))
        operations.append(RepairOperation(verification, f'Vérifier après {action}'))
    return AndroidRepairPlan(
        tuple(gaps),
        tuple(operations),
        'ENVIRONMENT_READY' if not gaps else 'TOOLCHAIN_PARTIAL',
    )
