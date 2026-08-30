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

def test_jdk_research_requires_checksum_and_official_source():
    from core.environment.user_space_repair import jdk_artifact_from_research
    from core.environment.research import EnvironmentResearchResult, EnvironmentMetadata, OfficialSource
    item=EnvironmentMetadata('21.0.1','lts','linux','x86_64','jdk.tar.gz','https://example.invalid/jdk.tar.gz',None)
    research=EnvironmentResearchResult([OfficialSource('Eclipse Adoptium','adoptium.net','https://api.adoptium.net/','https://api.adoptium.net/')],artifacts=[item],status='READY')
    assert jdk_artifact_from_research(research) is None

def test_jdk_research_rejects_wrong_architecture():
    from core.environment.user_space_repair import jdk_artifact_from_research
    from core.environment.research import EnvironmentResearchResult, EnvironmentMetadata, OfficialSource
    item=EnvironmentMetadata('21.0.1','lts','linux','aarch64','jdk.tar.gz','https://api.adoptium.net/jdk.tar.gz','a'*64)
    research=EnvironmentResearchResult([OfficialSource('Eclipse Adoptium','adoptium.net','https://api.adoptium.net/','https://api.adoptium.net/')],artifacts=[item],status='READY')
    assert jdk_artifact_from_research(research) is None

def test_preflight_rejects_system_destination():
    from core.environment.user_space_repair import preflight_user_space
    assert not preflight_user_space('/usr/local/jarvis').ok

def test_android_repair_operations_are_allowlisted():
    from core.environment.repair_engine import RepairEngine
    assert 'INSTALL_ANDROID_CMDLINE_TOOLS' in RepairEngine.ALLOWED
    assert 'VERIFY_FLUTTER_ANDROID_TOOLCHAIN' in RepairEngine.ALLOWED

def test_adoptium_provider_requires_complete_official_metadata():
    from core.environment.adoptium_provider import AdoptiumProvider
    assert AdoptiumProvider(lambda url: [{}]).research().status == 'NEEDS_RESEARCH'

def test_adoptium_provider_resolves_dynamic_metadata():
    from core.environment.adoptium_provider import AdoptiumProvider
    payload=[{'version': {'semver':'21.0.1'}, 'binary': {'package': {'name':'jdk.tar.gz','link':'https://api.adoptium.net/artifacts/jdk.tar.gz','checksum':'a'*64}}}]
    result=AdoptiumProvider(lambda url: {'available_lts_releases':[21]} if '/info/' in url else payload).research()
    assert result.status == 'READY' and result.artifacts[0].architecture == 'x86_64'

def test_android_provider_never_trusts_missing_checksum_as_verified():
    from core.environment.android_provider import AndroidOfficialProvider
    artifact=AndroidOfficialProvider(lambda *args: {'version':'35','download_url':'https://dl.google.com/android.zip'}).research('platforms')
    assert artifact is not None and not artifact.trusted

def test_artifact_resolution_is_gap_driven():
    from core.environment.artifact_resolution import ArtifactResolutionEngine
    engine=ArtifactResolutionEngine()
    reqs=engine.requirements_for(('MISSING_JAVAC','MISSING_ANDROID_CMDLINE_TOOLS'))
    assert [r.component for r in reqs] == ['JDK','cmdline-tools']

def test_final_validation_requires_every_component():
    from core.environment.final_validation import validate_final_toolchain
    assert validate_final_toolchain(flutter=True, dart=True).state == 'PARTIAL'
    assert validate_final_toolchain(**{name: True for name in ('flutter','dart','java','javac','java_home','android_sdk','adb','build_tools','platforms','cmdline_tools','licenses','path','flutter_doctor')}).state == 'ENVIRONMENT_READY'

def test_android_installer_has_typed_component_plan():
    from core.environment.installers.android_installer import AndroidInstaller
    plan = AndroidInstaller().plan_component('cmdline-tools')
    assert [step.action_type for step in plan.steps] == ['DOWNLOAD','VERIFY','EXTRACT','INSTALL','VERIFY_ANDROID_COMPONENT']

def test_android_installer_rejects_arbitrary_component():
    from core.environment.installers.android_installer import AndroidInstaller
    import pytest
    with pytest.raises(ValueError): AndroidInstaller().plan_component('run-shell')

def test_adoptium_network_failure_is_typed():
    from core.environment.adoptium_provider import AdoptiumProvider
    result = AdoptiumProvider(lambda _url: (_ for _ in ()).throw(TimeoutError('timeout'))).research()
    assert result.provider_state == 'NETWORK_UNAVAILABLE'

def test_adoptium_invalid_json_is_typed():
    from core.environment.adoptium_provider import AdoptiumProvider
    result = AdoptiumProvider(lambda _url: 'not-json').research()
    assert result.provider_state == 'INVALID_RESPONSE'

def test_metadata_cache_official_expiry_and_corruption(tmp_path):
    from core.environment.research import MetadataCache
    cache=MetadataCache(tmp_path, ttl=3600)
    cache.save_official('jdk', {'version':'21'}, source='https://adoptium.net')
    assert cache.load_official('jdk')['state'] == 'CACHED_OFFICIAL_METADATA'
    (tmp_path/'broken.json').write_text('{', encoding='utf-8')
    assert cache.load_official('broken') is None

def test_android_cmdline_requires_sdkmanager(tmp_path):
    from core.environment.android_sdk import AndroidSDKDiscovery
    root=tmp_path/'sdk'/'cmdline-tools'/'latest'; (root/'bin').mkdir(parents=True)
    status=AndroidSDKDiscovery([tmp_path/'sdk']).discover()
    assert status.cmdline_tools == 'MISSING'
    (root/'bin'/'sdkmanager').write_text('', encoding='utf-8')
    (root/'bin'/'sdkmanager').chmod(0o755)
    assert AndroidSDKDiscovery([tmp_path/'sdk']).discover().cmdline_tools == 'PRESENT'

def test_resolution_state_reports_network_unavailable():
    from core.environment.artifact_resolution import ArtifactResolutionEngine, ResolutionState
    from core.environment.adoptium_provider import AdoptiumProvider
    engine=ArtifactResolutionEngine(jdk_provider=AdoptiumProvider(lambda _url: (_ for _ in ()).throw(OSError('dns'))))
    result=engine.resolve_detailed(('MISSING_JAVAC',))
    assert result.state == ResolutionState.NETWORK_UNAVAILABLE

def test_readiness_distinguishes_partial_and_network_blocked():
    from core.environment.readiness import assess_environment, ReadinessState
    a=android(cmdline_tools='MISSING')
    sdk_obj=sdk()
    result=assess_environment(sdk=sdk_obj, android=a, java={'java':True,'javac':False,'java_home':False}, provider_state='NETWORK_UNAVAILABLE')
    assert result.state == ReadinessState.BLOCKED_NETWORK and 'MISSING_JAVAC' in result.gaps

def test_cached_metadata_policy_requires_checksum_for_adoptium():
    from core.environment.metadata_cache import inspect_cached_metadata, CachePolicy
    payload={'state':'CACHED_OFFICIAL_METADATA','timestamp':100,'source':'https://adoptium.net','metadata':{'architecture':'x86_64','download_url':'https://api.adoptium.net/jdk.tar.gz'}}
    assert inspect_cached_metadata(payload, provider='Eclipse Adoptium', allowed_hosts={'api.adoptium.net'}, now=100)[0] == CachePolicy.CORRUPTED_CACHE
