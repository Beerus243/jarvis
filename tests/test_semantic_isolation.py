import os
import subprocess
import sys


ROOT = os.path.dirname(os.path.dirname(__file__))


def run_clean_import(code):
    env = os.environ.copy()
    env.pop("GROQ_API_KEY", None)
    return subprocess.run(
        [sys.executable, "-c", code],
        cwd=ROOT,
        env=env,
        check=True,
        capture_output=True,
        text=True,
    )


def test_memory_import_without_sentence_transformers():
    result = run_clean_import(
        "import sys; import memory; "
        "assert 'sentence_transformers' not in sys.modules"
    )
    assert result.returncode == 0


def test_remember_import_does_not_load_semantic_model():
    result = run_clean_import(
        "import sys; from memory import remember; "
        "assert callable(remember); "
        "assert 'sentence_transformers' not in sys.modules"
    )
    assert result.returncode == 0


def test_user_profile_import_without_semantic_dependency():
    result = run_clean_import(
        "import sys; from core.user_profile import analyze_profile; "
        "assert callable(analyze_profile); "
        "assert 'sentence_transformers' not in sys.modules"
    )
    assert result.returncode == 0
