import shutil
import subprocess


APPLICATIONS = {
    "chrome": {
        "commands": [
            ["google-chrome"],
            ["google-chrome-stable"],
        ],
        "label": "Google Chrome",
    },

    "spotify": {
        "commands": [
            ["flatpak", "run", "com.spotify.Client"],
        ],
        "label": "Spotify",
    },

    "vscode": {
        "commands": [
            ["code"],
        ],
        "label": "Visual Studio Code",
    },

    "firefox": {
        "commands": [
            ["firefox"],
        ],
        "label": "Firefox",
    },

    "terminal": {
        "commands": [
            ["konsole"],
            ["gnome-terminal"],
            ["ptyxis"],
        ],
        "label": "Terminal",
    },
}


def is_command_available(command):
    """
    Vérifie si une commande existe sur le système.
    """

    executable = command[0]

    return shutil.which(executable) is not None


def is_application_available(name):
    """
    Vérifie si une application est disponible.
    """

    name = name.lower().strip()

    application = APPLICATIONS.get(name)

    if not application:
        return False

    for command in application["commands"]:

        if is_command_available(command):
            return True

    return False


def open_application(name):
    """
    Lance une application connue.
    """

    name = name.lower().strip()

    application = APPLICATIONS.get(name)

    if not application:

        return (
            False,
            "Je ne connais pas cette application."
        )

    for command in application["commands"]:

        if is_command_available(command):

            try:

                subprocess.Popen(
                    command,
                    stdout=subprocess.DEVNULL,
                    stderr=subprocess.DEVNULL
                )

                return (
                    True,
                    f"J'ouvre {application['label']}."
                )

            except OSError:

                return (
                    False,
                    f"Impossible de lancer {application['label']}."
                )

    return (
        False,
        f"{application['label']} n'est pas disponible "
        "sur ce système."
    )


def list_available_applications():

    available = []

    for name in APPLICATIONS:

        if is_application_available(name):

            available.append(name)

    return available