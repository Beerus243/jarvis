from core.environment.execution import ExecutionResult, ExecutionStatus
from core.environment.repair_engine import diagnose_failure, run_with_replan

def test_repair_decision_is_explicit():
    assert diagnose_failure(ExecutionResult('a',ExecutionStatus.FAILED),'javac').available
    assert not diagnose_failure(ExecutionResult('a',ExecutionStatus.SUCCESS),'javac').available

def test_replan_is_bounded():
    calls=[]
    def execute(plan): calls.append(plan); return [ExecutionResult('a',ExecutionStatus.FAILED)]
    result=run_with_replan('p',execute=execute,inspect=lambda: {},resolve_and_plan=lambda _: 'p2',max_replans=2)
    assert len(calls)==3 and result[0].status==ExecutionStatus.FAILED

def test_unknown_failure_is_not_repaired():
    result=diagnose_failure(ExecutionResult('a',ExecutionStatus.BLOCKED),'unknown')
    assert result.available is False
