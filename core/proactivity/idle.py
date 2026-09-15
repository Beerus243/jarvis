"""Notifications d'activité Wayland, sans lire les touches ni les positions.

Client minimal du protocole ext-idle-notify-v1 version 2 : aucun accès aux
protocoles clavier, pointeur, capture ou presse-papiers. Connexion dédiée.
"""
import os
from pathlib import Path
import socket
import struct
import threading
import time


def packet(object_id, opcode, payload=b''):
    return struct.pack('=II', object_id, ((8 + len(payload)) << 16) | opcode) + payload


def wire_string(value):
    raw = value.encode() + b'\0'
    return struct.pack('=I', len(raw)) + raw + b'\0' * (-len(raw) % 4)


class IdleMonitor:
    def __init__(self, clock=time.monotonic):
        self.clock = clock
        self._lock = threading.Lock()
        self._stop = threading.Event()
        self._socket = None
        self._thread = None
        self.ready = False
        self.last_input = None

    def start(self):
        if self._thread is None:
            self._thread = threading.Thread(target=self._run, name='jarvis-presence', daemon=True)
            self._thread.start()

    def stop(self):
        self._stop.set()
        connection = self._socket
        if connection:
            try:
                connection.shutdown(socket.SHUT_RDWR)
            except OSError:
                pass
        if self._thread:
            self._thread.join(timeout=2)

    def idle_seconds(self):
        with self._lock:
            return max(0, self.clock() - self.last_input) if self.ready and self.last_input is not None else None

    def _run(self):
        while not self._stop.is_set():
            try:
                self._connect()
            except (OSError, ValueError, KeyError, struct.error):
                pass
            finally:
                with self._lock:
                    self.ready, self.last_input = False, None
                if self._socket:
                    self._socket.close()
                    self._socket = None
            self._stop.wait(30)

    def _connect(self):
        display = os.getenv('WAYLAND_DISPLAY', 'wayland-0')
        path = Path(display) if display.startswith('/') else Path(os.environ['XDG_RUNTIME_DIR']) / display
        connection = socket.socket(socket.AF_UNIX, socket.SOCK_STREAM)
        self._socket = connection
        connection.settimeout(1)
        connection.connect(str(path))
        connection.sendall(packet(1, 1, struct.pack('=I', 2)))  # display.get_registry
        connection.sendall(packet(1, 0, struct.pack('=I', 3)))  # display.sync
        registry, buffer, bound = {}, b'', False
        deadline = self.clock() + 5
        while not self._stop.is_set():
            if not bound and self.clock() > deadline:
                raise ValueError('registry timeout')
            try:
                chunk = connection.recv(65536)
            except socket.timeout:
                continue
            if not chunk:
                return
            buffer += chunk
            if len(buffer) > 131072:
                raise ValueError('invalid frame buffer')
            while len(buffer) >= 8:
                object_id, word = struct.unpack('=II', buffer[:8])
                size, opcode = word >> 16, word & 65535
                if size < 8 or size % 4:
                    raise ValueError('invalid frame')
                if len(buffer) < size:
                    break
                payload, buffer = buffer[8:size], buffer[size:]
                if object_id == 1 and opcode == 0:
                    raise ValueError('compositor refused protocol')
                if object_id == 2 and opcode == 0:
                    name, length = struct.unpack('=II', payload[:8])
                    if length < 1 or 8 + length > len(payload):
                        raise ValueError('invalid global')
                    interface = payload[8:8+length-1].decode('ascii')
                    version = struct.unpack_from('=I', payload, 8 + ((length + 3) // 4) * 4)[0]
                    registry[interface] = (name, version)
                elif object_id == 3 and opcode == 0 and not bound:
                    seat, _ = registry['wl_seat']
                    notifier, version = registry['ext_idle_notifier_v1']
                    if version < 2:
                        raise ValueError('input idle protocol unavailable')
                    for name, interface, version, ident in [(seat, 'wl_seat', 1, 4), (notifier, 'ext_idle_notifier_v1', 2, 5)]:
                        connection.sendall(packet(2, 0, struct.pack('=I', name) + wire_string(interface) + struct.pack('=II', version, ident)))
                    # Zero timeout observes idle/resume transitions. Initial state
                    # remains UNKNOWN until a real resumed event has occurred.
                    connection.sendall(packet(5, 2, struct.pack('=III', 6, 0, 4)))
                    bound = True
                    with self._lock:
                        self.ready = True
                elif object_id == 6 and opcode == 1:
                    with self._lock:
                        self.last_input = self.clock()
