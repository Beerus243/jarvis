from structured_memory import (
    analyze_project_update,
    answer_project_question
)

messages = [
    "Mon backend utilise FastAPI",
    "Quel backend utilise mon projet ?",
    "Maintenant mon backend utilise Django",
    "Quel backend utilise mon projet ?",
]

for m in messages:
    print('Fabrice >', m)
    if m.lower().startswith(('mon', 'maintenant')):
        r = analyze_project_update(m)
    else:
        r = answer_project_question(m)
    print('JARVIS >', r)
    print()
