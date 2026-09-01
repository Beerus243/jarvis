from pathlib import Path
from unittest.mock import patch

from core.actions import PCAction
from core.actions.executor import execute_pc_action

def test_flatpak_desktop_discovery(tmp_path):
    from core import pc_discovery
    desktop = tmp_path / 'com.example.App.desktop'
    desktop.write_text('[Desktop Entry]\nName=Example Flatpak\nExec=flatpak run com.example.App\n', encoding='utf-8')
    root = tmp_path / 'flatpak'; root.mkdir()
    desktop.rename(root / desktop.name)
    with patch.object(pc_discovery, 'APPLICATION_ROOTS', (root,)):
        found = pc_discovery.discover_applications()
    assert any(item['name'] == 'Example Flatpak' for item in found)

def test_file_open_uses_xdg_open(tmp_path):
    target = tmp_path / 'rapport.txt'; target.write_text('ok')
    with patch('core.actions.executor.shutil.which', side_effect=lambda x: '/usr/bin/xdg-open' if x == 'xdg-open' else None), patch('core.actions.executor.subprocess.Popen') as popen:
        with patch('core.actions.executor.Path.home', return_value=tmp_path):
            result = execute_pc_action(PCAction('FILE_OPEN', {'path': str(target)}))
    assert result.success is True
    popen.assert_called_once_with(['xdg-open', str(target)])

def test_file_open_missing_file_fails(tmp_path):
    result = execute_pc_action(PCAction('FILE_OPEN', {'path': str(tmp_path / 'missing.txt')}))
    assert result.success is False and result.error == 'NOT_FOUND'
