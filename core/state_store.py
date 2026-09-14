"""État durable transactionnel des tâches, rappels et préférences V5."""
from contextlib import contextmanager
import json
import os
from pathlib import Path
import sqlite3
import threading

from config.settings import DATA_DIR

_transaction_lock = threading.RLock()


class StateStore:
    def __init__(self, path=None):
        self.path = Path(path or os.getenv('JARVIS_STATE_DB') or DATA_DIR / 'runtime.sqlite3')

    @contextmanager
    def transaction(self):
        # Sérialise aussi l'initialisation du mode WAL entre l'horloge et le dialogue.
        with _transaction_lock:
            with self._transaction() as connection:
                yield connection

    @contextmanager
    def _transaction(self):
        self.path.parent.mkdir(parents=True, exist_ok=True)
        connection = sqlite3.connect(self.path, timeout=10)
        try:
            connection.execute('PRAGMA journal_mode=WAL')
            connection.execute('CREATE TABLE IF NOT EXISTS records (namespace TEXT, key TEXT, value TEXT NOT NULL, PRIMARY KEY(namespace,key))')
            connection.execute('BEGIN IMMEDIATE')
            yield connection
            connection.commit()
        except BaseException:
            connection.rollback()
            raise
        finally:
            connection.close()

    def get(self, namespace, key, default=None):
        with self.transaction() as db:
            row = db.execute('SELECT value FROM records WHERE namespace=? AND key=?', (namespace, key)).fetchone()
            return json.loads(row[0]) if row else default

    def put(self, namespace, key, value):
        with self.transaction() as db:
            self._put(db, namespace, key, value)
        return value

    @staticmethod
    def _put(db, namespace, key, value):
        db.execute('INSERT INTO records VALUES (?,?,?) ON CONFLICT(namespace,key) DO UPDATE SET value=excluded.value',
                   (namespace, key, json.dumps(value, ensure_ascii=False)))

    def delete(self, namespace, key):
        with self.transaction() as db:
            db.execute('DELETE FROM records WHERE namespace=? AND key=?', (namespace, key))

    def items(self, namespace):
        with self.transaction() as db:
            return [(key, json.loads(value)) for key, value in db.execute(
                'SELECT key,value FROM records WHERE namespace=? ORDER BY key', (namespace,))]

    def mutate(self, namespace, key, transform, default=None):
        """Read-modify-write atomique. Le callback ne doit pas faire d'I/O externe."""
        with self.transaction() as db:
            row = db.execute('SELECT value FROM records WHERE namespace=? AND key=?', (namespace, key)).fetchone()
            value = transform(json.loads(row[0]) if row else default)
            if value is None:
                db.execute('DELETE FROM records WHERE namespace=? AND key=?', (namespace, key))
            else:
                self._put(db, namespace, key, value)
            return value


def get_store():
    return StateStore()
