from core.environment.execution import ExecutionResult, ExecutionStatus
def test_result_serializes_and_sanitizes():
    r=ExecutionResult('A1',ExecutionStatus.SUCCESS,stdout='token=secret')
    assert r.to_dict()['status']=='SUCCESS' and '[REDACTED]' in r.to_dict()['stdout']
