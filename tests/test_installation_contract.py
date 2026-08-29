from core.environment.installers import FlutterInstaller, InstallerRegistry, TrustedSource
from core.environment.execution import ExecutionStatus
def test_untrusted_installation_is_blocked():
    assert FlutterInstaller().install(confirmed=True, network_available=True).status == ExecutionStatus.BLOCKED
def test_source_and_registry_are_strict():
    assert TrustedSource('x','1','zip').approved() is False
    registry=InstallerRegistry(); registry.register(FlutterInstaller())
    assert registry.get('flutter') is not None
