from text_normalizer import normalize_text


def parse_project_information(message):

    text = normalize_text(message)

    # ========================================================
    # PYTHON
    # ========================================================

    python_patterns = [
        "developpe en python",
        "developpe avec python",
        "code en python",
        "code avec python",
        "utilise python",
        "utilise le langage python",
        "langage utilise python",
        "langage est python",
    ]

    for pattern in python_patterns:

        if pattern in text:

            return {
                "attribute": "langage",
                "value": "Python"
            }


    # ========================================================
    # JAVASCRIPT
    # ========================================================

    javascript_patterns = [
        "developpe en javascript",
        "developpe avec javascript",
        "code en javascript",
        "code avec javascript",
        "utilise javascript",
    ]

    for pattern in javascript_patterns:

        if pattern in text:

            return {
                "attribute": "langage",
                "value": "JavaScript"
            }


    # ========================================================
    # TYPESCRIPT
    # ========================================================

    typescript_patterns = [
        "developpe en typescript",
        "developpe avec typescript",
        "code en typescript",
        "code avec typescript",
        "utilise typescript",
    ]

    for pattern in typescript_patterns:

        if pattern in text:

            return {
                "attribute": "langage",
                "value": "TypeScript"
            }


    return None