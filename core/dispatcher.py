from tools.tools import open_browser, open_musique, get_time
from tools.applications import open_application, open_folder, open_website
from tools.projects import resolve_project, format_projects
from tools.projects import resolve_project
from actions.media import play_music
from tools.spotify import (
    play_track,
    pause,
    resume,
    next_track,
    previous_track,
)
from tools.browser import (
    open_url,
    search_web,
    search_wikipedia,
)
from core.actions import PCAction, execute_pc_action


def dispatch(intent):

    if intent == "SCREENSHOT":
        result = execute_pc_action(PCAction("SCREENSHOT"))
        return result

    # ========================================================
    # PROJETS — LISTER
    # ========================================================

    if intent == "LIST_PROJECTS":
        return True, format_projects()

    # ========================================================
    # ACTIONS STRUCTURÉES
    # ========================================================

    if isinstance(intent, dict):

        action = intent.get("action")

        if action in {
            "OPEN_APPLICATION", "CLOSE_APPLICATION", "OPEN_URL",
            "FILE_OPEN", "FILE_CREATE", "FILE_COPY", "FILE_MOVE", "FILE_DELETE",
            "VOLUME_UP", "VOLUME_DOWN", "VOLUME_MUTE", "MEDIA_PLAY", "MEDIA_PAUSE",
            "MEDIA_NEXT", "MEDIA_PREVIOUS",
        }:
            params = dict(intent)
            params.pop("action", None)
            result = execute_pc_action(PCAction(action, params))
            return result

        if action == "SCREENSHOT":
            result = execute_pc_action(PCAction("SCREENSHOT"))
            return result.success, result.message if result.success else result.error

        # ----------------------------------------------------
        # APPLICATION
        # ----------------------------------------------------

        if action == "OPEN_APPLICATION":
            return open_application(intent.get("target", ""))

        # ----------------------------------------------------
        # PROJET — OUVRIR DANS VS CODE
        # ----------------------------------------------------

        if action == "OPEN_PROJECT":

            project_name = intent.get("project", "")
            project = resolve_project(project_name)

            if not project:
                return (
                    False,
                    f"Je ne connais pas le projet « {project_name} »."
                )

            return open_application(
                "vscode",
                project["path"],
            )

        # ----------------------------------------------------
        # PROJET — OUVRIR DANS VS CODE
        # ----------------------------------------------------

        if action == "OPEN_PROJECT":

            project_name = intent.get("project", "")
            project = resolve_project(project_name)

            if not project:
                return (
                    False,
                    f"Je ne connais pas le projet « {project_name} »."
                )

            return open_application(
                "vscode",
                project["path"],
            )

        # ----------------------------------------------------
        # VS CODE
        # ----------------------------------------------------

        if action == "OPEN_VSCODE":

            target = intent.get("target") or "~/dev/jarvis"

            return open_application(
                "vscode",
                target,
            )

        # ----------------------------------------------------
        # SPOTIFY
        # ----------------------------------------------------

        if action in {
            "PLAY_MUSIC",
            "SEARCH_MUSIC",
        }:

            return play_track(
                title=intent.get("title"),
                artist=(
                    intent.get("artist")
                    or intent.get("query")
                ),
            )

        if action == "PAUSE_MUSIC":

            return pause()

        if action == "RESUME_MUSIC":

            return resume()

        if action == "NEXT_TRACK":

            return next_track()

        if action == "PREVIOUS_TRACK":

            return previous_track()

        # ----------------------------------------------------
        # NAVIGATION WEB
        # ----------------------------------------------------

        if action == "OPEN_URL":

            return open_url(
                intent.get("url", "")
            )

        if action == "SEARCH_WEB":

            return search_web(
                intent.get("query", "")
            )

        if action == "SEARCH_WIKIPEDIA":

            return search_wikipedia(
                intent.get("query", "")
            )

    # ========================================================
    # ANCIENNES INTENTIONS SIMPLES
    # ========================================================

    if intent == "GREETINGS":

        return (
            True,
            "Bonjour Fabrice. "
            "Je suis heureux de vous voir."
        )

    elif intent == "GET_TIME":

        heure = get_time()

        return (
            True,
            f"Il est actuellement {heure}",
        )

    elif intent == "OPEN_BROWSER":

        result = open_browser()

        if isinstance(result, tuple):
            return result

        return (
            bool(result),
            result,
        )

    elif intent == "OPEN_SPOTIFY":

        result = open_musique()

        if isinstance(result, tuple):
            return result

        return (
            bool(result),
            result,
        )

    elif intent == "PLAY_MUSIC":

        result = open_musique()

        if isinstance(result, tuple):
            return result

        return (
            bool(result),
            result,
        )

    elif intent == "OPEN_TERMINAL":

        return open_application(
            "terminal"
        )

    elif intent == "OPEN_VSCODE":

        return open_application(
            "vscode"
        )

    elif intent == "OPEN_FIREFOX":

        return open_application(
            "firefox"
        )

    elif intent == "OPEN_FOLDER":

        return open_folder(
            "Documents"
        )

    elif intent in {
        "OPEN_SITE",
        "OPEN_WEBSITE",
    }:

        return open_website(
            "https://www.google.com"
        )

    # ========================================================
    # AUCUNE ACTION RECONNUE
    # ========================================================

    return None
