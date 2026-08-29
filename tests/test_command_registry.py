from core.environment.command_registry import get_command
def test_registry_is_allowlist():
    assert get_command('verify_git') and get_command('rm') is None
