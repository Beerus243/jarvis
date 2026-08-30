#!/usr/bin/env python3
"""Read-only Flutter/Android environment audit."""
from pathlib import Path
import sys
ROOT=Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path: sys.path.insert(0,str(ROOT))
from core.environment import LocalSDKDiscovery, AndroidSDKDiscovery, analyze_flutter_toolchain, build_repair_plan

sdk=next(iter(LocalSDKDiscovery().discover()),None); android=AndroidSDKDiscovery().discover()
print('FLUTTER ANDROID ENVIRONMENT AUDIT')
print('FLUTTER:', 'READY' if sdk and sdk.flutter else 'MISSING')
print('DART:', 'READY' if sdk and sdk.dart else 'MISSING')
print('ANDROID_SDK_ROOT:', android.root or 'MISSING')
print('ADB:', android.adb, '(IN_PATH)' if android.adb_in_path else '(NOT_IN_PATH)')
print('BUILD_TOOLS:', android.build_tools); print('PLATFORMS:', android.platforms); print('CMDLINE_TOOLS:', android.cmdline_tools); print('LICENSES:', android.licenses)
if sdk:
    report=analyze_flutter_toolchain(sdk,android=android); print('TOOLCHAIN:', 'READY' if report.environment_ready else 'PARTIAL'); print('GAPS:', ', '.join(report.gaps) or 'NONE')
