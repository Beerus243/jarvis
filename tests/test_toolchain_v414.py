from types import SimpleNamespace
from core.environment.toolchain import analyze_flutter_toolchain
def sdk(path=True,flutter=True,dart=True): return SimpleNamespace(path_configured=path,flutter=flutter,dart=dart)
def android(**kw):
    d=dict(sdk='PRESENT',adb='PRESENT',build_tools='PRESENT',platforms='PRESENT',cmdline_tools='PRESENT',licenses='ACCEPTED'); d.update(kw); return SimpleNamespace(**d)
def java(**kw):
    d=dict(java='/usr/bin/java',javac='/usr/bin/javac',java_home='/jdk'); d.update(kw); return d
def test_complete_toolchain_ready():
    r=analyze_flutter_toolchain(sdk(),java=java(),android=android()); assert r.environment_ready and not r.gaps
def test_missing_javac_is_partial():
    r=analyze_flutter_toolchain(sdk(),java=java(javac=None),android=android()); assert r.sdk_ready and not r.android_toolchain_ready and 'MISSING_JAVAC' in r.gaps
def test_missing_android_component_is_gap():
    r=analyze_flutter_toolchain(sdk(),java=java(),android=android(build_tools='MISSING')); assert 'MISSING_ANDROID_BUILD_TOOLS' in r.gaps
def test_missing_flutter_path_proposes_repair():
    r=analyze_flutter_toolchain(sdk(path=False),java=java(),android=android()); assert 'CONFIGURE_PATH' in r.actions
