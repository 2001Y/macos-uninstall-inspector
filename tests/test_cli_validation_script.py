import subprocess
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]


def test_validation_script_succeeds_for_repo_examples():
    result = subprocess.run(
        [sys.executable, str(ROOT / "scripts" / "validate_examples.py")],
        cwd=ROOT,
        capture_output=True,
        text=True,
    )
    assert result.returncode == 0, result.stdout + result.stderr
    assert "validated" in result.stdout.lower()


def test_validation_script_succeeds_without_pythonpath():
    env = dict(__import__("os").environ)
    env.pop("PYTHONPATH", None)
    result = subprocess.run(
        [sys.executable, str(ROOT / "scripts" / "validate_examples.py")],
        cwd=ROOT,
        capture_output=True,
        text=True,
        env=env,
    )
    assert result.returncode == 0, result.stdout + result.stderr
    assert "validated" in result.stdout.lower()
