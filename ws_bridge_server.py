"""Compatibility launcher for the real Core; never starts a simulated bridge.

The existing jarvis.service already includes the WebSocket in --background mode.
Stop that service before using this standalone, microphone-free entry point.
"""
from main import main

if __name__ == '__main__':
    raise SystemExit(main(['--ui-only']))
