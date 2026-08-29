from core.environment.installers import InstallationPlan, InstallationStep
from core.environment.installation_engine import execute_installation_plan
from core.environment.execution import ExecutionStatus

def test_dry_run_never_calls_operations():
    plan=InstallationPlan('x',[InstallationStep('a','x','DOWNLOAD',1,[])])
    called=[]; report=execute_installation_plan(plan,dry_run=True,operations={'DOWNLOAD':lambda s:called.append(s)})
    assert report.results[0].status==ExecutionStatus.SKIPPED and not called

def test_confirmation_and_typed_operation():
    plan=InstallationPlan('x',[InstallationStep('a','x','PATH_UPDATE',1,[],requires_confirmation=True)])
    report=execute_installation_plan(plan,dry_run=False,confirmation_handler=lambda s:True,operations={'PATH_UPDATE':lambda s:None})
    assert report.results[0].status==ExecutionStatus.SUCCESS

def test_unknown_operation_is_blocked():
    plan=InstallationPlan('x',[InstallationStep('a','x','DOWNLOAD',1,[])])
    assert execute_installation_plan(plan,dry_run=False).results[0].status==ExecutionStatus.BLOCKED
