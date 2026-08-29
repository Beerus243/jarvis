from core.environment.command_registry import get_command
def test_verification_command_is_declared():
    assert get_command('verify_flutter').arguments == ('--version',)
