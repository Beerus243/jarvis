from core.environment.action_planner import plan_environment_setup
def test_unknown_is_blocked():
    p=plan_environment_setup('Flutter',{'commands':{'flutter':{'status':'UNKNOWN'}},'applications':{},'android':{}})
    assert p.blocked
