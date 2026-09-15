"""Instantané KWin en lecture seule via le Python système et dbus-next.

Un script éphémère est déchargé avant la sortie ; aucune installation KDE.
Exécuter directement avec /usr/bin/python3 (hors dépendances du venv vocal).
"""
import asyncio
import json
import os
from pathlib import Path
import tempfile
import uuid


async def snapshot():
    from dbus_next.aio import MessageBus
    from dbus_next.service import ServiceInterface, method
    from dbus_next import Message, MessageType
    future = asyncio.get_running_loop().create_future()
    service = 'org.jarvis.Snapshot.p' + str(os.getpid())
    plugin = 'jarvis-snapshot-' + uuid.uuid4().hex

    class Receiver(ServiceInterface):
        def __init__(self):
            super().__init__('org.jarvis.Snapshot')

        @method()
        def Publish(self, payload: 's') -> 's':
            if not future.done() and len(payload) <= 128 * 1024:
                future.set_result(payload)
            return 'ok'

    bus = await MessageBus().connect()
    await bus.request_name(service)
    bus.export('/Snapshot', Receiver())

    async def call(path, interface, member, signature='', body=None):
        reply = await asyncio.wait_for(bus.call(Message(destination='org.kde.KWin', path=path,
            interface=interface, member=member, signature=signature, body=body or [])), 2)
        if reply.message_type == MessageType.ERROR:
            raise RuntimeError('KWin snapshot unavailable')
        return reply.body

    with tempfile.TemporaryDirectory(prefix='jarvis-kwin-') as directory:
        script = Path(directory) / 'snapshot.js'
        script.write_text('''var windows = workspace.stackingOrder.map(function(w) {
            return {id: String(w.internalId), available: true, application: String(w.resourceClass),
                title: String(w.caption), pid: w.pid, active: w === workspace.activeWindow,
                closeable: false};
        });
        callDBus(SERVICE, "/Snapshot", "org.jarvis.Snapshot", "Publish",
            JSON.stringify({windows: windows}), function(reply) {});
        '''.replace('SERVICE', json.dumps(service)))
        try:
            result = await call('/Scripting', 'org.kde.kwin.Scripting', 'loadScript', 'ss', [str(script), plugin])
            script_id = result[0]
            if script_id < 0:
                raise RuntimeError('KWin script refused')
            await call(f'/Scripting/Script{script_id}', 'org.kde.kwin.Script', 'run')
            payload = await asyncio.wait_for(future, 2)
            return json.loads(payload)
        finally:
            try:
                await call('/Scripting', 'org.kde.kwin.Scripting', 'unloadScript', 's', [plugin])
            finally:
                bus.disconnect()


if __name__ == '__main__':
    try:
        print(json.dumps(asyncio.run(snapshot())))
    except Exception:
        print('{}')
        raise SystemExit(1)
