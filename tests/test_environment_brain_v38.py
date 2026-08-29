from core.intelligence import analyze
from core.response_planner import plan
def test_environment_request_is_local_decision():
    decision=analyze('prépare mon environnement Node.js')
    assert decision['type']=='ENVIRONMENT'
    assert plan(decision)['source']=='ENVIRONMENT'
