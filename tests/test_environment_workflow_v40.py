from core.environment.workflow import EnvironmentWorkflow
def test_workflow_dry_run_has_initial_state_and_no_execution():
    env={'commands':{},'applications':{},'android':{}}
    report=EnvironmentWorkflow(inspector=lambda:env).prepare('Flutter',dry_run=True)
    assert report.status=='PLANNED' and report.initial_state==env and report.results==[]
