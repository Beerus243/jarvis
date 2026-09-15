"""Présence native KDE en lecture seule ; inconnu n'est jamais actif."""
import re
import subprocess
import time


def _call(method):
    result = subprocess.run(['gdbus', 'call', '--session', '--dest', 'org.freedesktop.ScreenSaver',
        '--object-path', '/ScreenSaver', '--method', 'org.freedesktop.ScreenSaver.' + method],
        capture_output=True, text=True, timeout=2, check=True)
    return result.stdout.strip()


def read_presence(idle_monitor=None):
    try:
        locked = _call('GetActive')
        if locked not in {'(true,)', '(false,)'}:
            raise ValueError('unknown lock state')
        if locked == '(true,)':
            return {'state': 'locked', 'idle_seconds': None, 'observed_at': time.time(), 'source': 'KDE ScreenSaver'}
        if idle_monitor is not None:
            seconds = idle_monitor.idle_seconds()
            return {'state': 'unknown' if seconds is None else 'away' if seconds >= 120 else 'active',
                    'idle_seconds': seconds, 'observed_at': time.time(), 'source': 'Wayland input idle v2', 'locked': False}
        idle = re.fullmatch(r'\((?:uint32 )?(\+?\d+),\)', _call('GetSessionIdleTime'))
        if not idle:
            raise ValueError('unknown idle state')
        seconds = int(idle[1])
        return {'state': 'locked' if locked == '(true,)' else 'away' if seconds >= 120 else 'active',
                'idle_seconds': seconds, 'observed_at': time.time(), 'source': 'KDE ScreenSaver'}
    except (OSError, ValueError, subprocess.SubprocessError):
        return {'state': 'unknown', 'idle_seconds': None, 'observed_at': time.time(), 'source': 'KDE indisponible'}
