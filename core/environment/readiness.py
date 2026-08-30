"""Central, deterministic environment readiness decision."""
from __future__ import annotations
from dataclasses import dataclass
from enum import Enum

class ReadinessState(str, Enum):
    READY='READY'; REPAIRABLE_OFFLINE='REPAIRABLE_OFFLINE'; REPAIRABLE_ONLINE='REPAIRABLE_ONLINE'; BLOCKED_NETWORK='BLOCKED_NETWORK'; PARTIAL='PARTIAL'

@dataclass(frozen=True)
class EnvironmentReadiness:
    state: ReadinessState
    sdk_ready: bool
    android_toolchain_ready: bool
    jdk_ready: bool
    environment_ready: bool
    gaps: tuple[str, ...]
    repairability: dict[str, str]
    blocking_reasons: tuple[str, ...] = ()
    def to_dict(self):
        return {'state': self.state.value, 'sdk_ready': self.sdk_ready,
                'android_toolchain_ready': self.android_toolchain_ready,
                'jdk_ready': self.jdk_ready, 'environment_ready': self.environment_ready,
                'gaps': list(self.gaps), 'repairability': dict(self.repairability),
                'blocking_reasons': list(self.blocking_reasons)}

def assess_environment(*, sdk, android, java: dict, cache_components=(), provider_state='AVAILABLE'):
    gaps=[]
    sdk_ready=bool(sdk and sdk.flutter and sdk.dart)
    if not sdk_ready: gaps.extend(['MISSING_FLUTTER','MISSING_DART'])
    if not java.get('java'): gaps.append('MISSING_JAVA')
    if not java.get('javac'): gaps.append('MISSING_JAVAC')
    if not java.get('java_home'): gaps.append('MISSING_JAVA_HOME')
    if android.sdk != 'PRESENT': gaps.append('MISSING_ANDROID_SDK')
    if android.adb == 'MISSING': gaps.append('MISSING_ADB')
    if android.build_tools == 'MISSING': gaps.append('MISSING_ANDROID_BUILD_TOOLS')
    if android.platforms == 'MISSING': gaps.append('MISSING_ANDROID_PLATFORM')
    if android.cmdline_tools == 'MISSING': gaps.append('MISSING_ANDROID_CMDLINE_TOOLS')
    if android.licenses != 'ACCEPTED': gaps.append('LICENSE_STATE_UNKNOWN')
    jdk_ready=bool(java.get('java') and java.get('javac'))
    android_ready=android.sdk == 'PRESENT' and android.adb != 'MISSING' and android.build_tools != 'MISSING' and android.platforms != 'MISSING' and android.cmdline_tools != 'MISSING' and android.licenses == 'ACCEPTED'
    repairability={}
    cached=set(cache_components)
    for gap in gaps:
        repairability[gap] = 'AVAILABLE_OFFLINE' if gap in cached or (gap == 'MISSING_JAVA_HOME' and jdk_ready) else 'AVAILABLE_ONLINE'
    blocking=[]
    if provider_state == 'NETWORK_UNAVAILABLE' and any(v == 'AVAILABLE_ONLINE' for v in repairability.values()):
        blocking.append('Provider officiel inaccessible.')
    if not gaps: state=ReadinessState.READY
    elif blocking and not any(v == 'AVAILABLE_OFFLINE' for v in repairability.values()): state=ReadinessState.BLOCKED_NETWORK
    elif any(v == 'AVAILABLE_OFFLINE' for v in repairability.values()): state=ReadinessState.REPAIRABLE_OFFLINE
    elif provider_state == 'NETWORK_UNAVAILABLE': state=ReadinessState.BLOCKED_NETWORK
    else: state=ReadinessState.REPAIRABLE_ONLINE
    return EnvironmentReadiness(state, sdk_ready, android_ready, jdk_ready, sdk_ready and jdk_ready and android_ready, tuple(gaps), repairability, tuple(blocking))
