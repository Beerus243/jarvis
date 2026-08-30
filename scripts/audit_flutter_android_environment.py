#!/usr/bin/env python3
"""Read-only Flutter/Android environment audit."""
from pathlib import Path
import sys
ROOT=Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path: sys.path.insert(0,str(ROOT))
from core.environment import (LocalSDKDiscovery, AndroidSDKDiscovery, analyze_flutter_toolchain,
                              assess_environment, AdoptiumProvider, MetadataCache)
from core.environment.metadata_cache import inspect_cached_metadata
import os, shutil

sdk=next(iter(LocalSDKDiscovery().discover()),None); android=AndroidSDKDiscovery().discover()
print('FLUTTER ANDROID ENVIRONMENT AUDIT')
cache = MetadataCache(); cached = cache.load_official('adoptium-jdk-linux-x64')
if cached:
    policy, _ = inspect_cached_metadata(cached, provider='Eclipse Adoptium', allowed_hosts={'api.adoptium.net','adoptium.net','github.com','githubusercontent.com'})
    print('CACHE:', policy.value)
else:
    print('CACHE: NO_CACHE')
print('FLUTTER:', 'READY' if sdk and sdk.flutter else 'MISSING')
print('DART:', 'READY' if sdk and sdk.dart else 'MISSING')
print('ANDROID_SDK_ROOT:', android.root or 'MISSING')
print('ADB:', android.adb, '(IN_PATH)' if android.adb_in_path else '(NOT_IN_PATH)')
print('BUILD_TOOLS:', android.build_tools); print('PLATFORMS:', android.platforms); print('CMDLINE_TOOLS:', android.cmdline_tools); print('LICENSES:', android.licenses)
if sdk:
    java={'java':bool(shutil.which('java')), 'javac':bool(shutil.which('javac')), 'java_home':bool(os.environ.get('JAVA_HOME'))}
    report=analyze_flutter_toolchain(sdk,java=java,android=android); print('TOOLCHAIN:', 'READY' if report.environment_ready else 'PARTIAL'); print('GAPS:', ', '.join(report.gaps) or 'NONE')
    provider_state='AVAILABLE'
    try:
        import requests
        provider_state=AdoptiumProvider(fetcher=lambda url: requests.get(url,timeout=5).json(), cache=MetadataCache()).research().provider_state
    except Exception: provider_state='NETWORK_UNAVAILABLE'
    readiness=assess_environment(sdk=sdk,android=android,java=java,provider_state=provider_state)
    print('READINESS:', readiness.state.value)
    print('REPAIRABILITY:', ', '.join(f'{k}={v}' for k,v in readiness.repairability.items()) or 'NONE')
