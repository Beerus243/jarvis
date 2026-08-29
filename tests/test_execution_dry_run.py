from core.environment.action_planner import plan_environment_setup
from core.environment.action_executor import execute_plan
def test_dry_run_skips_without_execution():
    p=plan_environment_setup('Flutter',{'commands':{'flutter':{'status':'ABSENT'}},'applications':{},'android':{}})
    assert all(r.status.value=='SKIPPED' for r in execute_plan(p,dry_run=True))
