from brain import think

messages = [
    "Mon backend utilise FastAPI",
    "Quel backend utilise mon projet ?",
    "Maintenant mon backend utilise Django",
    "Quel backend utilise mon projet ?",
]

for m in messages:
    print('Fabrice >', m)
    r = think(m)
    print('JARVIS >', r)
    print()
