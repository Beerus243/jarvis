from pathlib import Path

def test_local_flutter_audit_bootstraps_project_root():
    source=Path('scripts/audit_local_flutter.py').read_text(encoding='utf-8')
    assert 'Path(__file__).resolve().parents[1]' in source
    assert 'sys.path.insert' in source
