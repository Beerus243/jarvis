from unittest.mock import patch

import pytest

from core.kwin_dbus_bridge import (
    INTERFACE_NAME,
    OBJECT_PATH,
    SERVICE_NAME,
    ping,
)


def test_dbus_endpoint_constants_are_stable():
    assert SERVICE_NAME == "org.jarvis.WindowContext"
    assert OBJECT_PATH == "/WindowContext"
    assert INTERFACE_NAME == "org.jarvis.WindowContext"


def test_ping_returns_pong_without_dbus_dependency():
    assert ping() == "pong"


def test_missing_binding_is_reported_by_service_start(monkeypatch):
    real_import = __import__

    def missing_dbus(name, *args, **kwargs):
        if name.startswith("dbus_next"):
            raise ImportError("missing")
        return real_import(name, *args, **kwargs)

    monkeypatch.setattr("builtins.__import__", missing_dbus)

    import asyncio
    from core.kwin_dbus_bridge import serve

    with pytest.raises(RuntimeError, match="dbus-next"):
        asyncio.run(serve())
