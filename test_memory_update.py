from structured_memory import (
    analyze_project_information_v2,
    get_project_attribute
)


print("================================")
print("TEST MÉMOIRE DYNAMIQUE")
print("================================")


print("\n1. Première information")

response = analyze_project_information_v2(
    "Mon backend utilise FastAPI"
)

print(response)


print("\n2. Même information")

response = analyze_project_information_v2(
    "Mon backend utilise FastAPI"
)

print(response)


print("\n3. Changement")

response = analyze_project_information_v2(
    "Mon backend utilise Django"
)

print(response)


print("\n4. Valeur actuelle")

backend = get_project_attribute(
    "backend"
)

print(
    "Backend actuel :",
    backend
)