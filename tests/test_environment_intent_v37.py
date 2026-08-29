from core.environment.intent import detect_environment_intent
def test_natural_language_profiles():
    assert detect_environment_intent('prépare-moi un environnement Flutter').profile=='flutter_development'
    assert detect_environment_intent("j'ai besoin d'un environnement Next.js").profile=='nextjs'
    assert detect_environment_intent('prépare Node.js').profile=='node'
    assert detect_environment_intent('prépare Java').profile=='java'
def test_alias_and_version():
    i=detect_environment_intent('installe node v20'); assert i.profile=='node' and i.requested_version=='20'
def test_unknown_is_none(): assert detect_environment_intent('ouvre Spotify') is None
