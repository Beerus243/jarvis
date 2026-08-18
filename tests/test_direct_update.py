from memory.structured_memory import (
    get_project_attribute,
    update_project_attribute
)

print("================================")
print("TEST UPDATE DIRECT")
print("================================")

print("Avant :", get_project_attribute("backend"))

update_project_attribute(
    "backend",
    "Django"
)

print("Après :", get_project_attribute("backend"))