"""Exécute la suite configurée dans une copie temporaire, avec le Python courant."""
from pathlib import Path
import shutil
import subprocess
import sys
import tempfile


def main():
    root = Path(__file__).resolve().parents[1]
    with tempfile.TemporaryDirectory(prefix='jarvis-tests-') as directory:
        destination = Path(directory)
        for name in ('core', 'config', 'memory', 'personality', 'voice', 'tools', 'actions', 'ai', 'tests', 'data', 'scripts'):
            if (root/name).is_dir():
                shutil.copytree(root/name, destination/name,
                    ignore=shutil.ignore_patterns('__pycache__', '*.sqlite3*', '*.lock'))
        for name in ('main.py', 'pytest.ini', 'requirements.txt'):
            shutil.copy2(root/name, destination/name)
        return subprocess.run([sys.executable, '-m', 'pytest', '-q', *sys.argv[1:]], cwd=destination).returncode


if __name__ == '__main__':
    raise SystemExit(main())
