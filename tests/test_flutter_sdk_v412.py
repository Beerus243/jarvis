from pathlib import Path
from core.environment.local_sdks import LocalSDKDiscovery
from core.environment.installers.flutter_installer import FlutterInstaller
from core.environment.installation_engine import InstallationEngine
from core.environment.execution import ExecutionResult, ExecutionStatus
from core.environment.path_config import ConfigureUserPath
from core.environment.shell_profile import UserShellProfile

def sdk(tmp_path, dart=True, flutter=True):
    root=tmp_path/'flutter'; (root/'bin').mkdir(parents=True)
    if flutter: (root/'bin/flutter').write_text('x')
    if dart: (root/'bin/dart').write_text('x')
    return root
def test_extracted_sdk_without_path_is_detected(tmp_path,monkeypatch):
    root=sdk(tmp_path); monkeypatch.setenv('PATH',''); item=LocalSDKDiscovery([root]).discover()[0]; assert item.state=='EXTRACTED_NOT_CONFIGURED'
def test_configured_sdk_is_ready(tmp_path,monkeypatch):
    root=sdk(tmp_path); monkeypatch.setenv('PATH',str(root/'bin')); assert LocalSDKDiscovery([root]).discover()[0].state=='READY'
def test_missing_dart_is_partial(tmp_path):
    assert LocalSDKDiscovery([sdk(tmp_path,dart=False)]).discover()[0].state=='PARTIAL'
def test_existing_sdk_plan_has_no_download(tmp_path):
    assert [s.action_type for s in FlutterInstaller().plan_existing().steps]==['CONFIGURE_PATH','VERIFY_FLUTTER','VERIFY_DART']
def test_shell_profile_selection(tmp_path):
    assert UserShellProfile('zsh',tmp_path).path_file==tmp_path/'.zshrc'; assert UserShellProfile('fish',tmp_path).path_file==tmp_path/'.config/fish/config.fish'
def test_path_failure_stops_verification(tmp_path):
    root=sdk(tmp_path)
    class Bad: 
        def apply(self,p): return False
    report=InstallationEngine(path_config=Bad(),allowed_root=tmp_path).execute(FlutterInstaller().plan_existing(),sdk_root=root,dry_run=False,confirmation_handler=lambda s:True)
    assert report.results[-1].status==ExecutionStatus.FAILED and len(report.results)==1
