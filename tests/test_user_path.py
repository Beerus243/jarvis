from pathlib import Path
import pytest
from core.environment.user_path import prepare_path_update, apply_user_path_update

def test_prepare_path_update_is_explicit(tmp_path):
    update=prepare_path_update(Path.home())
    assert update['requires_confirmation'] is True
    assert apply_user_path_update(update, confirmed=False, profile=Path.home()/'profile') is False

def test_path_traversal_rejected(tmp_path):
    with pytest.raises(ValueError): prepare_path_update('/etc')
