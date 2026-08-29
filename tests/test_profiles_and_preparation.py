from core.environment.profiles import DEFAULT_PROFILES, EnvironmentProfile, EnvironmentProfileRegistry
from core.environment.preparation import EnvironmentPreparationEngine
from core.environment.gap_analysis import analyze_gaps

def test_profile_aliases_and_duplicates():
    assert DEFAULT_PROFILES.resolve('next.js').id == 'nextjs'
    registry=EnvironmentProfileRegistry()
    registry.register(EnvironmentProfile('x','X'))
    try: registry.register(EnvironmentProfile('x','X2')); assert False
    except ValueError: pass

def test_preparation_plan_is_structured():
    env={'commands':{'flutter':{'status':'PRESENT'},'dart':{'status':'PRESENT'},'java':{'status':'PRESENT'},'javac':{'status':'PRESENT'},'adb':{'status':'PRESENT'},'git':{'status':'PRESENT'}},'applications':{},'android':{'android_sdk':{'status':'PRESENT'},'android_studio':{'status':'PRESENT'}}}
    plan=EnvironmentPreparationEngine().prepare('Flutter',env)
    assert plan.gaps.readiness == 'READY'
    assert plan.to_dict()['execution_plan']['profile'] == 'flutter_development'
