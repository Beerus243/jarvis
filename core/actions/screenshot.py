from pathlib import Path
import shutil
import subprocess
from .models import ActionResult

class ScreenCapture:
    def __init__(self, destination=None, runner=subprocess.run):
        self.destination = Path(destination or Path.home() / "Pictures" / "Jarvis")
        self.runner = runner

    def capture(self):
        if not shutil.which("spectacle"):
            return ActionResult("SCREENSHOT", False, "Capture d'écran indisponible.", error="SCREENSHOT_UNAVAILABLE")
        self.destination.mkdir(parents=True, exist_ok=True)
        target = self.destination / "screenshot.png"
        try:
            result = self.runner(["spectacle", "-b", "-n", "-o", str(target)], check=False, capture_output=True, text=True, timeout=10)
            if result.returncode != 0 or not target.is_file():
                return ActionResult("SCREENSHOT", False, "La capture d'écran a échoué.", error="CAPTURE_FAILED")
            return ActionResult("SCREENSHOT", True, "Capture d'écran effectuée.", artifact_path=str(target))
        except (OSError, subprocess.SubprocessError) as exc:
            return ActionResult("SCREENSHOT", False, "Capture d'écran indisponible.", error=str(exc))
