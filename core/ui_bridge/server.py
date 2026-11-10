"""Loopback-only WebSocket transport hosted by the real JARVIS lifecycle."""
import asyncio
from collections import OrderedDict
from contextlib import nullcontext
from http import HTTPStatus
import json
import logging
import os
import threading
import uuid
from . import adapter, events

log = logging.getLogger(__name__)


def validate(raw):
    value = json.loads(raw)
    if not isinstance(value, dict):
        raise ValueError('Objet JSON attendu.')
    kind = value.get('type')
    if kind == 'session.subscribe':
        if type(value.get('protocolVersion')) is not int or value['protocolVersion'] not in {1, 2}:
            raise ValueError('Version de protocole incompatible.')
        conversation_id = value.get('conversationId', 'default')
        if not isinstance(conversation_id, str) or not 1 <= len(conversation_id) <= 100:
            raise ValueError('Identifiant de conversation invalide.')
        value['conversationId'] = conversation_id
    elif kind == 'command.send':
        text = value.get('text')
        if not isinstance(text, str) or not text.strip() or len(text) > 2000:
            raise ValueError('Commande attendue : 1 à 2000 caractères.')
        value['text'] = text.strip()
        request_id = value.get('requestId')
        if request_id is not None and (not isinstance(request_id, str) or not 1 <= len(request_id) <= 100):
            raise ValueError('Identifiant de requête invalide.')
        value['requestId'] = request_id or uuid.uuid4().hex
        origin = value.get('origin', 'ui_text')
        if origin not in events.ORIGINS:
            raise ValueError('Origine de requête invalide.')
        value['origin'] = origin
        conversation_id = value.get('conversationId')
        if conversation_id is not None and (not isinstance(conversation_id, str) or not 1 <= len(conversation_id) <= 100):
            raise ValueError('Identifiant de conversation invalide.')
    elif kind in {'confirmation.respond', 'task.cancel'}:
        if not isinstance(value.get('id'), str) or not 1 <= len(value['id']) <= 100:
            raise ValueError('Identifiant invalide.')
        if kind == 'confirmation.respond' and type(value.get('approved')) is not bool:
            raise ValueError('Décision booléenne attendue.')
    elif kind == 'voice.speak':
        text = value.get('text')
        if not isinstance(text, str) or not text.strip() or len(text) > 4000:
            raise ValueError('Réponse audio attendue : 1 à 4000 caractères.')
        value['text'] = text.strip()
    elif kind in {'conversation.create', 'conversation.select'}:
        conversation_id = value.get('conversationId')
        if not isinstance(conversation_id, str) or not 1 <= len(conversation_id) <= 100:
            raise ValueError('Identifiant de conversation invalide.')
    elif kind not in {'voice.start', 'voice.stop'}:
        raise ValueError('Type de commande inconnu.')
    if kind in {'voice.start', 'voice.stop', 'voice.speak', 'confirmation.respond', 'task.cancel'}:
        value['requestId'] = value.get('requestId') or uuid.uuid4().hex
        origin = value.get('origin', 'ui_voice' if kind.startswith('voice.') else 'ui_text')
        if origin not in events.ORIGINS:
            raise ValueError('Origine de requête invalide.')
        value['origin'] = origin
    return value


class UIBridge:
    def __init__(self, port=None):
        self.port = int(os.environ.get('JARVIS_UI_PORT', '8765')) if port is None else port
        self.origins = [item.strip() for item in os.environ.get(
            'JARVIS_UI_ORIGINS', 'http://localhost:3000,http://127.0.0.1:3000').split(',') if item.strip()]
        self.clients = set()
        self.client_conversations = {}
        self.ready = threading.Event()
        self.error = None
        self.loop = None
        self.thread = None
        self.operation = None
        self.requests = OrderedDict()
        self.latest = {}
        self.previous = {'tasks': {}, 'agents': {}, 'confirmations': {}}
        self.system = None

    def start(self):
        # Fail here if the dependency is missing; never silently substitute a demo.
        from websockets.asyncio.server import serve  # noqa: F401
        self.thread = threading.Thread(target=self._thread, name='jarvis-ui', daemon=True)
        self.thread.start()
        if not self.ready.wait(10):
            raise RuntimeError('Démarrage WebSocket trop long.')
        if self.error:
            raise self.error
        return self

    def stop(self):
        if self.loop and self.loop.is_running():
            self.loop.call_soon_threadsafe(self.stopped.set)
        if self.thread:
            self.thread.join(timeout=5)

    def _thread(self):
        try:
            asyncio.run(self.run())
        except Exception as error:
            self.error = error
            log.exception('JARVIS UI bridge stopped')
        finally:
            self.ready.set()

    def _publish(self, event):
        scoped_types = {'message.updated', 'command.updated', 'tool.updated',
                        'confirmation.required', 'confirmation.resolved'}
        for queue in tuple(self.clients):
            if event.get('type') in scoped_types and (
                    event.get('conversationId') or 'default') != self.client_conversations.get(queue):
                continue
            if event.get('requestId') and event.get('type') in {
                    'state.changed', 'voice.state', 'transcription.updated', 'activity.created'} and (
                    event.get('conversationId') or 'default') != self.client_conversations.get(queue):
                continue
            if queue.full():
                # A slow browser must reconnect for a complete snapshot.
                while not queue.empty():
                    queue.get_nowait()
                queue.put_nowait(None)
                self.clients.discard(queue)
            else:
                queue.put_nowait(event)

    async def refresh(self):
        current = await asyncio.to_thread(adapter.snapshot)
        self.latest = current
        for name, event_type, key in [('tasks', 'task.updated', 'task'), ('agents', 'agent.updated', 'agent'),
                                      ('confirmations', 'confirmation.required', 'confirmation')]:
            items = {item['id']: item for item in current[name]}
            old = self.previous[name]
            if name == 'confirmations':
                for identifier in old.keys() - items.keys():
                    events.publish({'type': 'confirmation.resolved', 'id': identifier})
            for identifier, item in items.items():
                if old.get(identifier) != item:
                    events.publish({'type': event_type, key: item})
            self.previous[name] = items

    async def poll(self):
        counter = 0
        while True:
            if not self.clients:
                await asyncio.sleep(1)
                continue
            try:
                await self.refresh()
                if counter % 3 == 0:
                    self.system = await asyncio.to_thread(adapter.system_snapshot)
                    if self.system is not None:
                        events.publish({'type': 'system.updated', 'system': self.system})
                counter += 1
            except Exception:
                log.exception('UI snapshot unavailable')
            await asyncio.sleep(1)

    async def execute(self, command, queue):
        request_id = command.get('requestId')
        origin = command.get('origin', 'ui_voice' if command['type'].startswith('voice.') else 'ui_text')
        text = command.get('text', command['type'])
        conversation_id = command.get('conversationId')
        with events.request_scope(request_id, origin, conversation_id):
            try:
                if command['type'] != 'command.send':
                    events.command(request_id, origin, text, 'received', conversation_id=conversation_id)
                    events.command(request_id, origin, text, 'started', conversation_id=conversation_id)
                if command['type'] == 'confirmation.respond':
                    events.state('executing', 'Traitement de la confirmation')
                if command['type'] == 'command.send' and conversation_id:
                    from core.conversation import conversation_scope
                    conversation_context = conversation_scope(conversation_id)
                else:
                    conversation_context = nullcontext()
                with conversation_context:
                    await asyncio.to_thread(adapter.dispatch, command)
                if command['type'] == 'command.send':
                    self.requests[request_id]['status'] = 'completed'
                elif command['type'] == 'confirmation.respond':
                    events.command(request_id, origin, text, 'completed', conversation_id=conversation_id)
                elif command['type'] == 'voice.speak':
                    self.requests[request_id]['status'] = 'speaking'
                elif command['type'] == 'voice.start':
                    self.requests[request_id]['status'] = 'started'
                else:
                    events.command(request_id, origin, text, 'completed', conversation_id=conversation_id)
                    self.requests[request_id]['status'] = 'completed'
            except Exception as error:
                if command['type'] != 'command.send':
                    events.command(request_id, origin, text, 'failed', conversation_id=conversation_id, detail=error)
                    self.requests[request_id]['status'] = 'failed'
                if command['type'] == 'command.send':
                    if self.requests[request_id].get('status') != 'failed':
                        events.command(request_id, origin, text, 'failed', conversation_id=conversation_id, detail=error)
                    self.requests[request_id]['status'] = 'failed'
                self.notice(queue, str(error))
                events.activity(str(error), status='error')
            finally:
                if command['type'] == 'confirmation.respond':
                    events.state('idle', 'JARVIS prêt')
                try:
                    await self.refresh()
                    if command['type'] == 'confirmation.respond':
                        for item in self.latest.get('confirmations', []):
                            self.enqueue(queue, {'type': 'confirmation.required', 'confirmation': item})
                except Exception:
                    log.exception('UI refresh failed')

    @staticmethod
    def enqueue(queue, event):
        if not queue.full():
            queue.put_nowait(event)

    def notice(self, queue, message):
        event = {'type': 'notification.created', 'notification': {
            'id': uuid.uuid4().hex, 'title': 'JARVIS Core', 'message': message,
            'timestamp': events.now(), 'kind': 'warning', 'read': False}}
        if queue in self.clients:
            events.publish(event)
        else:
            self.enqueue(queue, event)

    def receive_command(self, command, queue):
        request_id = command['requestId']
        origin = command['origin']
        text = command['text']
        conversation_id = command.get('conversationId')
        fingerprint = json.dumps(
            {'text': text, 'origin': origin, 'conversationId': conversation_id},
            ensure_ascii=False, sort_keys=True,
        )
        previous = self.requests.get(request_id)
        if previous is not None:
            if previous['fingerprint'] != fingerprint:
                with events.request_scope(request_id, origin, conversation_id):
                    events.command(request_id, origin, text, 'failed', detail='Identifiant déjà utilisé pour une autre commande.')
                    self.notice(queue, 'Cet identifiant de requête est déjà associé à une autre commande.')
            else:
                events.command(request_id, origin, text, previous['status'], detail='Commande déjà reçue; aucune nouvelle exécution.')
            return

        self.requests[request_id] = {'fingerprint': fingerprint, 'status': 'received'}
        events.command(request_id, origin, text, 'received', conversation_id=conversation_id)
        if self.operation and not self.operation.done():
            self.requests[request_id]['status'] = 'failed'
            with events.request_scope(request_id, origin, conversation_id):
                events.command(request_id, origin, text, 'failed', detail='Une autre commande est déjà en cours.')
                self.notice(queue, 'Une commande est déjà en cours. Réessayez après sa réponse.')
            return
        self.requests[request_id]['status'] = 'started'
        self.operation = asyncio.create_task(self.execute(command, queue))

        if len(self.requests) > 2048:
            for old_id in list(self.requests)[:len(self.requests) - 2048]:
                self.requests.pop(old_id, None)

    async def receive_control(self, command, queue):
        request_id = command['requestId']
        origin = command.get('origin', 'ui_voice' if command['type'].startswith('voice.') else 'ui_text')
        text = command.get('text', command['type'])
        conversation_id = command.get('conversationId', 'default')
        fingerprint = json.dumps(
            {key: value for key, value in command.items() if key != 'requestId'},
            ensure_ascii=False, sort_keys=True,
        )
        previous = self.requests.get(request_id)
        if previous is not None:
            if previous['fingerprint'] != fingerprint:
                with events.request_scope(request_id, origin, conversation_id):
                    events.command(request_id, origin, text, 'failed', detail='Identifiant déjà utilisé pour une autre commande.')
                    self.notice(queue, 'Cet identifiant de requête est déjà associé à une autre commande.')
            else:
                with events.request_scope(request_id, origin, conversation_id):
                    events.command(request_id, origin, text, previous['status'], detail='Commande déjà reçue; aucune nouvelle exécution.')
            return
        self.requests[request_id] = {'fingerprint': fingerprint, 'status': 'received'}
        await self.execute(command, queue)

    def conversation_event(self, conversation_id, *, reset=False):
        from core.conversation import (
            conversation_scope, list_conversations, load_conversation,
            load_operation_events,
        )

        events_out = []
        if reset:
            events_out.append({'type': 'session.reset'})
            events_out.append({
                'type': 'session.capabilities', 'voice': events.get_voice() is not None,
                'eventId': uuid.uuid4().hex, 'sequence': events.sequence(),
                'historical': False, 'timestamp': events.now(),
            })
        items = list_conversations()
        events_out.append({
            'type': 'conversation.index', 'activeId': conversation_id,
            'items': items, 'eventId': uuid.uuid4().hex,
            'sequence': events.sequence(), 'historical': True,
            'timestamp': events.now(),
        })
        with conversation_scope(conversation_id):
            records = load_conversation()
        messages_by_key = {}
        for index, record in enumerate(records):
            role = record.get('role')
            if role not in {'user', 'assistant', 'jarvis'}:
                continue
            message = {
                'id': record.get('id') or f'{conversation_id}-{index}',
                'role': 'user' if role == 'user' else 'jarvis',
                'text': str(record.get('message', '')),
                'timestamp': record.get('timestamp') or events.now(),
                'status': 'sent', 'tools': [],
                **{key: record[key] for key in ('requestId', 'origin') if record.get(key)},
            }
            key = (message.get('requestId'), message['role']) if message.get('requestId') else ('history', message['id'])
            messages_by_key[key] = message
        operation_events = load_operation_events(conversation_id)
        for event in operation_events:
            if event.get('type') == 'message.updated':
                message = event['message']
                key = (event.get('requestId'), message['role']) if event.get('requestId') else ('history', message['id'])
                messages_by_key[key] = {**message, 'requestId': event.get('requestId'),
                                        'origin': event.get('origin')}
        messages = sorted(messages_by_key.values(), key=lambda message: message.get('timestamp', ''))[-100:]
        events_out.append({
            'type': 'conversation.history', 'conversationId': conversation_id,
            'messages': messages, 'eventId': uuid.uuid4().hex,
            'sequence': events.sequence(), 'historical': True,
            'timestamp': events.now(),
        })
        events_out.extend(
            {**event, 'historical': True}
            for event in operation_events
            if event.get('type') != 'message.updated'
        )
        return events_out

    def select_conversation(self, queue, conversation_id, *, create=False):
        from core.conversation import create_conversation, list_conversations

        if create:
            create_conversation(conversation_id)
        elif conversation_id not in {item['id'] for item in list_conversations()}:
            self.notice(queue, 'Conversation introuvable.')
            return
        self.client_conversations[queue] = conversation_id
        for event in self.conversation_event(conversation_id, reset=True):
            self.enqueue(queue, event)

    async def sender(self, socket, queue):
        while True:
            event = await queue.get()
            if event is None:
                await socket.close(code=1013, reason='Reconnect for current state')
                return
            await socket.send(json.dumps(event, ensure_ascii=False))

    async def handler(self, socket):
        from websockets.exceptions import ConnectionClosed

        queue = asyncio.Queue(maxsize=512)
        sender = asyncio.create_task(self.sender(socket, queue))
        subscribed = False
        try:
            async for raw in socket:
                try:
                    command = validate(raw)
                    if command['type'] == 'session.subscribe':
                        if subscribed:
                            raise ValueError('Session déjà abonnée.')
                        conversation_id = command['conversationId']
                        from core.conversation import list_conversations
                        if conversation_id not in {item['id'] for item in list_conversations()}:
                            conversation_id = 'default'
                        self.client_conversations[queue] = conversation_id
                        # No await between capturing the history and attaching the client.
                        self.enqueue(queue, {'type': 'session.reset'})
                        self.enqueue(queue, {'type': 'session.capabilities', 'voice': events.get_voice() is not None})
                        for event in events.snapshot():
                            scoped_types = {'message.updated', 'command.updated', 'tool.updated',
                                            'confirmation.required', 'confirmation.resolved'}
                            if event.get('type') not in scoped_types or event.get('conversationId') == conversation_id:
                                if event.get('type') != 'message.updated':
                                    self.enqueue(queue, event)
                            elif event.get('type') == 'activity.created' and event.get('requestId') and event.get('conversationId') == conversation_id:
                                self.enqueue(queue, event)
                        for event in self.conversation_event(conversation_id):
                            self.enqueue(queue, event)
                        for name, event_type, key in [('tasks', 'task.updated', 'task'), ('agents', 'agent.updated', 'agent'),
                                                      ('confirmations', 'confirmation.required', 'confirmation')]:
                            for item in self.latest.get(name, []):
                                self.enqueue(queue, {'type': event_type, key: item})
                        if self.system:
                            self.enqueue(queue, {'type': 'system.updated', 'system': self.system})
                        self.enqueue(queue, {
                            'type': 'session.synced', 'throughSequence': events.sequence(),
                            'eventId': uuid.uuid4().hex, 'historical': True,
                            'timestamp': events.now(),
                        })
                        self.clients.add(queue)
                        subscribed = True
                    elif not subscribed:
                        raise ValueError('Abonnez la session avant une commande.')
                    elif command['type'] == 'command.send':
                        self.receive_command(command, queue)
                    elif command['type'] == 'conversation.create':
                        self.select_conversation(queue, command['conversationId'], create=True)
                    elif command['type'] == 'conversation.select':
                        self.select_conversation(queue, command['conversationId'])
                    elif command['type'] in {'task.cancel', 'voice.start', 'voice.stop', 'voice.speak'}:
                        await self.receive_control(command, queue)
                    elif command['type'] == 'confirmation.respond':
                        await self.receive_control(command, queue)
                    elif self.operation and not self.operation.done():
                        raise ValueError('Une commande est déjà en cours. Réessayez après sa réponse.')
                    else:
                        self.operation = asyncio.create_task(self.execute(command, queue))
                except (ValueError, TypeError) as error:
                    self.notice(queue, str(error))
        except ConnectionClosed:
            pass
        finally:
            self.clients.discard(queue)
            self.client_conversations.pop(queue, None)
            sender.cancel()
            await asyncio.gather(sender, return_exceptions=True)

    async def run(self):
        from websockets.asyncio.server import serve
        events.initialize_sequence()
        self.loop = asyncio.get_running_loop()
        self.stopped = asyncio.Event()
        def forward(event):
            if event.get('type') == 'command.updated':
                command = event['command']
                current = self.requests.get(command['requestId'])
                if current is not None and command['status'] in {'completed', 'failed'}:
                    current['status'] = command['status']
            if not self.loop.is_closed():
                self.loop.call_soon_threadsafe(self._publish, event)
        def check_path(connection, request):
            if request.path != '/ws':
                return connection.respond(HTTPStatus.NOT_FOUND, 'Use /ws\n')
        unsubscribe = events.subscribe(forward)
        poller = None
        try:
            async with serve(self.handler, '127.0.0.1', self.port,
                             origins=[*self.origins, None], process_request=check_path,
                             max_size=16384, max_queue=16, close_timeout=2) as server:
                self.port = server.sockets[0].getsockname()[1]
                poller = asyncio.create_task(self.poll())
                self.ready.set()
                print(f'JARVIS UI > ws://127.0.0.1:{self.port}/ws (Core réel)', flush=True)
                await self.stopped.wait()
        finally:
            unsubscribe()
            if poller:
                poller.cancel()
                await asyncio.gather(poller, return_exceptions=True)
