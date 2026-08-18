from memory.project_responses import format_project_update


print(
    format_project_update(
        "backend",
        None,
        "FastAPI"
    )
)

print(
    format_project_update(
        "backend",
        "FastAPI",
        "FastAPI"
    )
)

print(
    format_project_update(
        "backend",
        "FastAPI",
        "Django"
    )
)

print(
    format_project_update(
        "frontend",
        "React",
        "Next.js"
    )
)

print(
    format_project_update(
        "base_de_donnees",
        "PostgreSQL",
        "MongoDB"
    )
)