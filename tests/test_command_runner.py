from unittest.mock import patch
from core.environment.command_registry import get_command
from core.environment.command_runner import run_command
def test_runner_uses_non_shell():
    with patch('core.environment.command_runner.subprocess.run') as run:
        run.return_value.returncode=0; run.return_value.stdout='ok'; run.return_value.stderr=''
        assert run_command(get_command('verify_git')).status.value=='SUCCESS'
        assert run.call_args.kwargs['shell'] is False
