import unicodedata
import re
from core.command_understanding import normalize_command, resolve_command_terms


def _normalize_text(text: str) -> str:
    text = text.lower()

    text = unicodedata.normalize("NFD", text)
    text = "".join(
        ch for ch in text
        if not unicodedata.combining(ch)
    )

    text = re.sub(
        r"[^\w\s]",
        " ",
        text
    )

    text = re.sub(
        r"\s+",
        " ",
        text
    ).strip()

    return text


def detect_work_environment_intent(message):
    """
    Détecte les formulations naturelles demandant
    de préparer l'environnement de travail.

    Cette fonction ne déclenche aucune action.
    Elle retourne uniquement l'intention WORK_ENVIRONMENT
    ou None.
    """

    message = _normalize_text(
        resolve_command_terms(message)["normalized_terms"]
    )

    work_environment_phrases = {
        "au boulot",
        "au travail",
        "go bosser",
        "on bosse",
        "je vais bosser",
        "je vais travailler",
        "je vais coder",
        "on va bosser",
        "on va travailler",
        "on va coder",
        "c est parti pour le boulot",
        "c est parti pour travailler",
        "c est parti pour coder",
        "c est parti on bosse",
        "prepare mon environnement de travail",
        "lance mon environnement de travail",
        "ouvre mon environnement de travail",
        "prepare mon environnement de dev",
        "lance mon environnement de dev",
        "lancer mon environnement de dev",
        "ouvre mon environnement de dev",
        "ouvrir mon environnement de dev",
        "prepare moi pour coder",
        "prepare moi pour travailler",
        "mets moi en condition pour travailler",
        "mets moi en condition pour coder",
    }

    if message in work_environment_phrases:
        return "WORK_ENVIRONMENT"

    return None


def detect_intent(message):
    # Actions PC à paramètres (dossiers, fichiers, services web).
    from core.action_parser import _pc_action
    if (pc_action := _pc_action(message)):
        return pc_action

    message = _normalize_text(resolve_command_terms(message)["normalized_terms"])

    screenshot_phrases = ("fais une capture d ecran", "fais une capture ecran", "capture mon ecran", "capture l ecran", "prends une capture d ecran", "prends une capture ecran", "screenshot", "capture ecran")
    if any(phrase in message for phrase in screenshot_phrases):
        return "SCREENSHOT"

    # Les phrases interrogatives générales ne sont pas des commandes locales.
    if message.startswith(("pourquoi ", "comment ", "qu est ce ", "est ce que ")):
        return None

    # Actions PC déterministes (les paramètres restent structurés).
    app = re.match(r"^(?:ouvre|lance|demarre|démarre|open|launch)\s+(?:mon\s+)?(firefox|vscode|vs code|visual studio code|terminal|konsole)$", message)
    if app:
        target = app.group(1).replace("google chrome", "chrome").replace("vs code", "vscode").replace("visual studio code", "vscode")
        return {"action": "OPEN_APPLICATION", "target": target}
    close = re.match(r"^(?:ferme|quitte|close|quit)\s+(?:l application|la fenetre|le logiciel|)?\s*(firefox|chrome|google chrome|spotify|vscode|vs code|terminal|konsole)$", message)
    if close:
        target = close.group(1).replace("google chrome", "chrome").replace("vs code", "vscode")
        return {"action": "CLOSE_APPLICATION", "target": target}
    if message in {"monte le son", "augmente le volume", "augmente le son"}: return {"action": "VOLUME_UP"}
    if message in {"baisse le son", "diminue le volume", "diminue le son"}: return {"action": "VOLUME_DOWN"}
    if message in {"coupe le son", "mets en muet", "mute"}: return {"action": "VOLUME_MUTE"}
    if message in {"mets en pause", "pause la musique", "mets la musique en pause"}: return {"action": "MEDIA_PAUSE"}
    if message in {"reprends", "reprends la musique", "reprends spotify"}: return {"action": "MEDIA_PLAY"}
    if message in {"passe au morceau suivant", "morceau suivant", "suivant"}: return {"action": "MEDIA_NEXT"}
    if message in {"morceau précédent", "morceau precedent", "précédent", "precedent"}: return {"action": "MEDIA_PREVIOUS"}

    # ========================================================
    # CHROME / NAVIGATEUR
    # ========================================================

    chrome_phrases = [
        "ouvre chrome",
        "ouvre google chrome",
        "lance chrome",
        "lance google chrome",
        "demarre chrome",
        "demarre google chrome",
        "ouvre internet",
        "open chrome",
        "open browser",
        "launch chrome",
        "ouvre le navigateur",
        "ouvre mon navigateur",
        "lance le navigateur",
        "lance mon navigateur",
    ]

    if any(
        phrase in message
        for phrase in chrome_phrases
    ):
        return "OPEN_BROWSER"

    # ========================================================
    # SPOTIFY
    # ========================================================

    spotify_phrases = [
        "ouvre spotify",
        "open spotify",
        "lance spotify",
        "demarre spotify",
        "ouvre la musique",
        "lance la musique",
    ]

    if any(
        phrase in message
        for phrase in spotify_phrases
    ):
        return "OPEN_SPOTIFY"


    # ========================================================
    # CONTRÔLES SPOTIFY
    # ========================================================

    pause_phrases = [
        "pause la musique",
        "mets la musique en pause",
        "met la musique en pause",
        "mets spotify en pause",
        "met spotify en pause",
        "pause spotify",
        "arrete la musique",
        "arrête la musique",
    ]

    if any(phrase == message for phrase in pause_phrases):
        return {"action": "PAUSE_MUSIC"}

    resume_phrases = [
        "reprends la musique",
        "reprend la musique",
        "reprends spotify",
        "reprend spotify",
        "reprends la lecture",
        "reprend la lecture",
        "continue la musique",
        "continue spotify",
    ]

    if any(phrase == message for phrase in resume_phrases):
        return {"action": "RESUME_MUSIC"}

    next_phrases = [
        "morceau suivant",
        "chanson suivante",
        "musique suivante",
        "passe au morceau suivant",
        "passe a la chanson suivante",
        "passe à la chanson suivante",
        "suivant",
        "next",
    ]

    if any(phrase == message for phrase in next_phrases):
        return {"action": "NEXT_TRACK"}

    previous_phrases = [
        "morceau precedent",
        "morceau précédente",
        "chanson precedente",
        "chanson précédente",
        "musique precedente",
        "musique précédente",
        "passe au morceau precedent",
        "passe au morceau précédent",
        "passe a la chanson precedente",
        "passe à la chanson précédente",
        "precedent",
        "précédent",
        "previous",
    ]

    if any(phrase == message for phrase in previous_phrases):
        return {"action": "PREVIOUS_TRACK"}

    # ========================================================
    # LECTURE D'UN ARTISTE (PLAY_MUSIC avec artiste)
    # ========================================================

    play_music_match = re.match(
        r"^(?:mets|joue)(?: moi)?(?: du| de la| des)? (.+)$",
        message,
    )

    if play_music_match:
        artist = play_music_match.group(1).strip()
        if artist:
            return {"action": "PLAY_MUSIC", "artist": artist}
        
    # ========================================================
    # FIREFOX
    # ========================================================

    firefox_phrases = [
        "ouvre firefox",
        "lance firefox",
        "demarre firefox",
    ]

    if any(
        phrase in message
        for phrase in firefox_phrases
    ):
        return "OPEN_FIREFOX"

    # ========================================================
    # PROJETS — LISTER LES PROJETS
    # ========================================================

    list_projects_phrases = [
        "quels sont mes projets",
        "quel sont mes projets",
        "liste mes projets",
        "liste des projets",
        "affiche mes projets",
        "montre moi mes projets",
        "montre-moi mes projets",
        "mes projets",
        "mes projets actuels",
    ]

    if any(
        phrase == message
        for phrase in list_projects_phrases
    ):
        return "LIST_PROJECTS"

    # ========================================================
    # PROJET — OUVRIR DANS VS CODE
    # ========================================================
    #
    # Exemples :
    #
    #   ouvre mon projet jarvis
    #   ouvre le projet jarvis
    #   ouvre mon projet "jarvis"
    #   lance mon projet jarvis
    #   ouvre mon projet JARVIS
    #
    # Le nom du projet est transmis au dispatcher.
    # La résolution du chemin est centralisée dans tools.projects.
    # ========================================================

    project_match = re.match(
        r'^(?:open|launch|start) '
        r'(?:(?:mon|my|le|the) )?'
        r'(?:projet|project) '
        r'["\']?(.+?)["\']?$',
        message,
    )

    if project_match:
        project = project_match.group(1).strip()

        if project:
            return {
                "action": "OPEN_PROJECT",
                "project": project,
            }

    # ========================================================
    # VISUAL STUDIO CODE
    # ========================================================

    vscode_phrases = [
        "ouvre visual studio code",
        "lance visual studio code",
        "demarre visual studio code",
        "ouvre vscode",
        "lance vscode",
        "demarre vscode",
        "ouvre vs code",
        "lance vs code",
    ]

    if any(
        phrase in message
        for phrase in vscode_phrases
    ):
        return "OPEN_VSCODE"

    # ========================================================
    # TERMINAL
    # ========================================================

    terminal_phrases = [
        "ouvre le terminal",
        "ouvre terminal",
        "lance le terminal",
        "lance terminal",
        "demarre le terminal",
        "demarre terminal",
        "ouvre konsole",
        "lance konsole",
    ]

    if any(
        phrase in message
        for phrase in terminal_phrases
    ):
        return "OPEN_TERMINAL"

    if "ouvre" in message and any(value in message for value in ("dossier", "documents", "repertoire", "répertoire")):
        return "OPEN_FOLDER"
    if "ouvre" in message and any(value in message for value in ("site", "youtube", "github", "google")):
        return "OPEN_WEBSITE"

    # ========================================================
    # SALUTATIONS
    # ========================================================

    greetings = [
        "bonjour",
        "salut",
        "hey",
        "bro",
        "coucou",
    ]

    if any(
        mot in message.split()
        for mot in greetings
    ):
        return "GREETINGS"

    # ========================================================
    # HEURE
    # ========================================================

    if any(
        mot in message.split()
        for mot in [
            "heure",
            "time",
            "horloge",
        ]
    ):
        return "GET_TIME"

    # ========================================================
    # COMPATIBILITÉ ANCIEN SYSTÈME
    # ========================================================

    if any(
        mot in message.split()
        for mot in [
            "navigateur",
            "internet",
            "browser",
        ]
    ):
        return "OPEN_BROWSER"


    return None
