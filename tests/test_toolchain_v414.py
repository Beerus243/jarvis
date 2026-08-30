from types import SimpleNamespace
from core.environment.toolchain import analyze_flutter_toolchain
from core.environment.repair_plan import build_repair_plan
from core.environment.repair_engine import RepairEngine
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
def test_complete_android_repair_has_no_actions():
    from core.environment.android_repair import build_android_repair_plan
    assert build_android_repair_plan(android()).state=='ENVIRONMENT_READY'
def test_android_component_repairs_are_targeted():
    from core.environment.android_repair import build_android_repair_plan
    p=build_android_repair_plan(android(adb='MISSING',build_tools='MISSING')); assert [x.action for x in p.operations]==['INSTALL_ANDROID_PLATFORM_TOOLS','VERIFY_ADB','INSTALL_ANDROID_BUILD_TOOLS','VERIFY_BUILD_TOOLS']
def test_repair_plan_is_targeted():
    p=build_repair_plan(sdk(),analyze_flutter_toolchain(sdk(),java=java(javac=None),android=android(build_tools='MISSING'))); assert [a.action for a in p.actions]==['INSTALL_JDK','INSTALL_ANDROID_COMPONENT']
def test_repair_engine_dry_run_has_no_handler_call():
    called=[]; plan=type('P',(),{'actions':[type('A',(),{'action':'CONFIGURE_PATH','requires_confirmation':True})()]})()
    report=RepairEngine({'CONFIGURE_PATH':lambda op: called.append(1)}).execute(plan,dry_run=True); assert not called and report.results[0].status.value=='SKIPPED'
def test_repair_engine_requires_confirmation():
    plan=type('P',(),{'actions':[type('A',(),{'action':'CONFIGURE_PATH','requires_confirmation':True})()]})(); report=RepairEngine({'CONFIGURE_PATH':lambda op: None}).execute(plan,dry_run=False,confirmation_handler=lambda op:False); assert report.results[0].status.value=='CANCELLED'
def test_repair_engine_stops_on_failure():
    plan=type('P',(),{'actions':[type('A',(),{'action':'VERIFY','requires_confirmation':False}),type('A',(),{'action':'CONFIGURE_PATH','requires_confirmation':False})()]})(); report=RepairEngine({'VERIFY':lambda op: (_ for _ in ()).throw(RuntimeError('x')),'CONFIGURE_PATH':lambda op: None}).execute(plan,dry_run=False); assert len(report.results)==1 and report.results[0].status.value=='FAILED'
