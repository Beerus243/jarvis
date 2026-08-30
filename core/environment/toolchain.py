from dataclasses import dataclass
from .resolvers import JavaEnvironmentResolver
from .android_sdk import AndroidSDKDiscovery

@dataclass(frozen=True)
class FlutterToolchainReport:
    sdk_ready: bool; android_toolchain_ready: bool; environment_ready: bool; gaps: tuple[str,...]; actions: tuple[str,...]; java: dict; android: object
    def to_dict(self): return {'sdk_ready':self.sdk_ready,'android_toolchain_ready':self.android_toolchain_ready,'environment_ready':self.environment_ready,'gaps':list(self.gaps),'actions':list(self.actions),'java':self.java,'android':self.android.to_dict()}

def analyze_flutter_toolchain(sdk, *, java=None, android=None, path=None):
    java=java or JavaEnvironmentResolver().resolve(); android=android or AndroidSDKDiscovery().discover()
    gaps=[]; actions=[]
    if not sdk.flutter: gaps.append('MISSING_FLUTTER')
    if not sdk.dart: gaps.append('MISSING_DART')
    if not sdk.path_configured: gaps.append('MISSING_FLUTTER_PATH'); actions.append('CONFIGURE_PATH')
    if not java.get('java'): gaps.append('MISSING_JAVA')
    if not java.get('javac'): gaps.append('MISSING_JAVAC')
    if not java.get('java_home'): gaps.append('MISSING_JAVA_HOME')
    if android.sdk!='PRESENT': gaps.append('MISSING_ANDROID_SDK')
    if android.adb=='MISSING': gaps.append('MISSING_ADB')
    if android.build_tools=='MISSING': gaps.append('MISSING_ANDROID_BUILD_TOOLS')
    if android.platforms=='MISSING': gaps.append('MISSING_ANDROID_PLATFORM')
    if android.cmdline_tools=='MISSING': gaps.append('MISSING_ANDROID_CMDLINE_TOOLS')
    if android.licenses!='ACCEPTED': gaps.append('LICENSE_STATE_UNKNOWN')
    sdk_ready=sdk.flutter and sdk.dart
    android_ready=sdk_ready and not any(g.startswith(('MISSING_JAVA','MISSING_JAVAC','MISSING_ANDROID','MISSING_ADB')) for g in gaps)
    return FlutterToolchainReport(sdk_ready,android_ready,sdk_ready and android_ready,tuple(gaps),tuple(dict.fromkeys(actions)),java,android)
