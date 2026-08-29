from core.environment.installers import FlutterInstaller, InstallerRegistry, TrustedSource
from core.environment.execution import ExecutionStatus
def test_untrusted_installation_is_blocked(monkeypatch):
    # Keep the contract independent from an optional Flutter installation on
    # the host running the tests.
    monkeypatch.setattr(FlutterInstaller, 'inspect', lambda self: {'flutter': None})
    assert FlutterInstaller().install(confirmed=True, network_available=True).status == ExecutionStatus.BLOCKED
def test_source_and_registry_are_strict():
    assert TrustedSource('x','1','zip').approved() is False
    registry=InstallerRegistry(); registry.register(FlutterInstaller())
    assert registry.get('flutter') is not None
