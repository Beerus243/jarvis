from structured_memory import (
    update_project,
    get_project,
    get_project_attribute
)


update_project(
    "nom",
    "JARVIS"
)

update_project(
    "langage",
    "Python"
)

update_project(
    "type",
    "assistant IA"
)


print(
    get_project()
)

print(
    get_project_attribute("langage")
)