from core.environment.preparation_service import EnvironmentPreparationService
def test_provider_unavailable_is_safe(): assert EnvironmentPreparationService().prepare('Flutter')['status']=='NEEDS_RESEARCH'
def test_fake_provider_feeds_plan():
    class Fake:
        def research(self, request): return type('R',(),{'status':'READY'})()
    assert EnvironmentPreparationService(Fake()).prepare('Flutter')['status']=='PLANNED'
