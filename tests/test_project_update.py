from memory.structured_memory import (
    analyze_project_update,
    get_project_attribute
)

print("================================")
print("TEST UPDATE BACKEND")
print("================================")

print(
    "Avant :",
    get_project_attribute("backend")
)

response = analyze_project_update(
    "Mon backend utilise Django"
)

print(
    "Réponse :",
    response
)

print(
    "Après :",
    get_project_attribute("backend")
)
