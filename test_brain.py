from brain import think
from conversation import get_history


print("================================")
print("       TEST DU CERVEAU")
print("================================")


tests = [
    "quelle heure est-il",
    "",
    "bonjour",
    "merci",
]


for message in tests:

    print(f"\nFabrice > {message}")

    response = think(message)

    print(f"JARVIS > {response}")


print("\n================================")
print("       HISTORIQUE")
print("================================")

for message in get_history():

    print(f"{message['role']} : {message['message']}")
