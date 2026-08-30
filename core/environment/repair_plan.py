from dataclasses import dataclass

@dataclass(frozen=True)
class RepairAction:
    action: str; reason: str; requires_confirmation: bool = True

@dataclass(frozen=True)
class EnvironmentRepairPlan:
    state: str; gaps: tuple[str,...]; actions: tuple[RepairAction,...]
    def to_dict(self): return {'state':self.state,'gaps':list(self.gaps),'actions':[a.__dict__ for a in self.actions]}

def build_repair_plan(sdk, toolchain):
    gaps=tuple(toolchain.gaps); actions=[]
    for gap in gaps:
        mapping={'MISSING_FLUTTER_PATH':('CONFIGURE_PATH','Flutter SDK détecté sans PATH'),
                 'MISSING_JAVA_HOME':('CONFIGURE_ENVIRONMENT','JAVA_HOME absent'),
                 'MISSING_ANDROID_SDK':('INSTALL_ANDROID_COMPONENT','Android SDK absent'),
                 'MISSING_ADB':('INSTALL_ANDROID_COMPONENT','ADB absent'),
                 'MISSING_ANDROID_BUILD_TOOLS':('INSTALL_ANDROID_COMPONENT','Build tools absents'),
                 'MISSING_ANDROID_PLATFORM':('INSTALL_ANDROID_COMPONENT','Plateforme Android absente'),
                 'MISSING_ANDROID_CMDLINE_TOOLS':('INSTALL_ANDROID_COMPONENT','Command-line tools absents'),
                 'MISSING_JAVAC':('INSTALL_JDK','JDK/javac absent'),
                 'LICENSE_STATE_UNKNOWN':('ACCEPT_ANDROID_LICENSES','État des licences inconnu')}
        if gap in mapping: actions.append(RepairAction(*mapping[gap]))
    state='ENVIRONMENT_READY' if toolchain.environment_ready else 'TOOLCHAIN_PARTIAL' if toolchain.sdk_ready else 'BROKEN'
    return EnvironmentRepairPlan(state,gaps,tuple(actions))
