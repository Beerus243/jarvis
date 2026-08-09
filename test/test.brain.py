from brain import think


def test_unknown_command():

    response = think("bonjour")

    assert response is not None