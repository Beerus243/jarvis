from core.environment.installers import FlutterInstaller
from core.environment.resolvers import JavaEnvironmentResolver, AndroidEnvironmentResolver, FlutterEnvironmentResolver
from core.environment.execution import ExecutionStatus

def test_resolvers_are_read_only(monkeypatch):
    monkeypatch.setattr('shutil.which', lambda name: None)
    assert JavaEnvironmentResolver().resolve()['status'] == 'MISSING'
    assert AndroidEnvironmentResolver().resolve()['status'] in {'MISSING', 'MISCONFIGURED'}
    assert FlutterEnvironmentResolver().resolve()['status'] == 'MISSING'

def test_flutter_installer_requires_confirmation_and_never_installs():
    installer=FlutterInstaller('/tmp/jarvis-flutter-test')
    assert installer.install().status == ExecutionStatus.WAITING_CONFIRMATION
    assert installer.install(confirmed=True, network_available=True).status == ExecutionStatus.BLOCKED
