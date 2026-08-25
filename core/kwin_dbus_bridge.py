"""Petit service D-Bus du contexte KWin.

Le service est volontairement séparé du venv JARVIS : Fedora fournit
dbus-next au Python système, mais pas à l'environnement Python 3.12 du
projet. Cette étape ne transporte encore aucune fenêtre.
"""

import asyncio
import sys

SERVICE_NAME = "org.jarvis.WindowContext"
OBJECT_PATH = "/WindowContext"
INTERFACE_NAME = "org.jarvis.WindowContext"


def ping():
    return "pong"


async def serve():
    try:
        from dbus_next.aio import MessageBus
        from dbus_next.service import ServiceInterface, method
    except ImportError as error:
        raise RuntimeError("dbus-next est requis dans le Python du service") from error

    class WindowContextInterface(ServiceInterface):
        def __init__(self):
            super().__init__(INTERFACE_NAME)

        @method()
        def Ping(self) -> "s":
            print("JARVIS_DBus_PING_RECEIVED", flush=True)
            return ping()

    bus = await MessageBus().connect()
    await bus.request_name(SERVICE_NAME)
    bus.export(OBJECT_PATH, WindowContextInterface())
    print("JARVIS_DBus_READY", flush=True)
    await asyncio.get_running_loop().create_future()


def main():
    if sys.version_info < (3, 10):
        raise SystemExit("Le bridge nécessite Python 3.10 ou plus récent.")
    asyncio.run(serve())


if __name__ == "__main__":
    main()
