from unittest.mock import patch

from core.kwin_context import (
    can_close_window,
    get_active_window,
    get_kwin_context,
    get_window_by_pid,
    list_windows,
)


WINDOWS = [
    {"application": "VS Code", "title": "brain.py", "pid": 3086, "active": True, "closeable": False},
    {"application": "Chrome", "title": "KDE", "pid": 5404, "active": False, "closeable": False},
]


def test_kwin_provider_normalizes_active_window_and_list():
    context = get_kwin_context({"windows": WINDOWS})
    assert context["active_window"]["application"] == "VS Code"
    assert context["active_window"]["title"] == "brain.py"
    assert context["active_window"]["pid"] == 3086
    assert len(context["windows"]) == 2


def test_kwin_unavailable_is_explicit_and_safe():
    with patch("core.kwin_context._read_provider", return_value=None):
        context = get_kwin_context()
    assert context["active_window"]["available"] is False
    assert context["active_window"]["application"] is None
    assert context["windows"] == []


def test_window_helpers_and_closeability_are_read_only():
    assert get_active_window({"windows": WINDOWS})["active"] is True
    assert get_window_by_pid(5404, {"windows": WINDOWS})["application"] == "Chrome"
    assert list_windows({"windows": WINDOWS})[0]["pid"] == 3086
    assert can_close_window(WINDOWS[0]) is False
    assert can_close_window({**WINDOWS[0], "available": True, "closeable": True}) is True


def test_pc_context_contains_kwin_sections():
    with patch("core.pc_context.get_kwin_context", return_value={
        "active_window": {"available": False, "application": None, "title": None, "pid": None, "active": False, "closeable": False},
        "windows": [],
    }), patch("core.pc_context._process_snapshot", return_value=[]):
        from core.pc_context import get_pc_context
        context = get_pc_context()
    assert context["active_window"]["available"] is False
    assert context["windows"] == []

def test_kwin_dbus_reader_parses_read_only_payload():
    from core.kwin_context import _fetch_via_dbus
    values = {
        ('/KWin', 'org.kde.KWin.windowList'): 'uint32 42 43',
        ('/KWin', 'org.kde.KWin.activeWindow'): 'uint32 43',
        ('/Window_42', 'org.kde.KWin.Window.caption'): '"Terminal"',
        ('/Window_42', 'org.kde.KWin.Window.windowClass'): '"konsole"',
        ('/Window_42', 'org.kde.KWin.Window.geometry'): '0,0,100,100',
        ('/Window_43', 'org.kde.KWin.Window.caption'): '"Firefox"',
        ('/Window_43', 'org.kde.KWin.Window.windowClass'): '"firefox"',
        ('/Window_43', 'org.kde.KWin.Window.geometry'): '0,0,100,100',
    }
    with patch('core.kwin_context._dbus_call', side_effect=lambda p,m: values.get((p,m))), patch('core.kwin_context.shutil.which', return_value='/usr/bin/dbus-send'):
        result = _fetch_via_dbus()
    assert result['active_window_id'] == 43 and result['windows'][1]['active'] is True
