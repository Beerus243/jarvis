from text_normalizer import normalize_text


def parse_project_information(message):

    text = normalize_text(message)
        # ========================================================
    # UNE QUESTION N'EST PAS UNE INFORMATION À MÉMORISER
    # ========================================================

    question_markers = [
        "quel",
        "quelle",
        "quels",
        "quelles",
        "comment",
        "pourquoi",
        "ou",
        "quand",
        "qui",
        "est-ce que",
    ]

    if (
        text.endswith("?")
        or any(
            text.startswith(marker + " ")
            for marker in question_markers
        )
    ):
        return None

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
        "code le projet avec python",
        "code mon projet avec python",
        "ai code le projet avec python",
        "ai code mon projet avec python",
        "langage utilise est python",
        "langage utilise : python",
        "langage utilise python",
        "le langage utilise est python",
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
        "code le projet avec javascript",
        "code mon projet avec javascript",
        "langage utilise est javascript",
        "le langage utilise est javascript",
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
        "code le projet avec typescript",
        "code mon projet avec typescript",
        "langage utilise est typescript",
        "le langage utilise est typescript",
    ]

    for pattern in typescript_patterns:

        if pattern in text:

            return {
                "attribute": "langage",
                "value": "TypeScript"
            }

    # ============================================================
    # BACKEND / FRAMEWORK
    # ============================================================

    backends = [
        "fastapi",
        "django",
        "flask",
        "nestjs",
        "express",
    ]

    backend_names = {
        "fastapi": "FastAPI",
        "django": "Django",
        "flask": "Flask",
        "nestjs": "NestJS",
        "express": "Express",
    }

    if "backend" in text:
        for backend in backends:
            if backend in text:
                return {
                    "attribute": "backend",
                    "value": backend_names[backend]
                }

    # ============================================================
    # BASE DE DONNÉES
    # ============================================================

    databases = [
        "postgresql",
        "postgres",
        "mysql",
        "mongodb",
        "sqlite",
    ]

    for database in databases:

        if database in text:

            if database == "postgres":
                value = "PostgreSQL"

            elif database == "postgresql":
                value = "PostgreSQL"

            elif database == "mysql":
                value = "MySQL"

            elif database == "mongodb":
                value = "MongoDB"

            elif database == "sqlite":
                value = "SQLite"

            return {
                "attribute": "base_de_donnees",
                "value": value
            }


    # ============================================================
    # FRONTEND
    # ============================================================

    frontends = [
        "react",
        "next.js",
        "vue",
        "angular",
        "flutter",
    ]

    for frontend in frontends:

        if frontend in text:

            if frontend == "react":
                value = "React"

            elif frontend == "next.js":
                value = "Next.js"

            elif frontend == "vue":
                value = "Vue"

            elif frontend == "angular":
                value = "Angular"

            elif frontend == "flutter":
                value = "Flutter"

            return {
                "attribute": "frontend",
                "value": value
            }

    return None
