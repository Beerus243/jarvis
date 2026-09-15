from pathlib import Path
from datetime import datetime
from uuid import uuid4
import shutil
import subprocess
from .models import ActionResult

class ScreenCapture:
    def __init__(self, destination=None, runner=subprocess.run, *, timeout=20):
        self.announce_path = destination is None
        self.destination = Path(destination or Path.home() / "Pictures" / "Jarvis")
        self.runner = runner
        self.timeout = timeout

    def capture(self, scope="screen"):
        flags = {"screen": "--fullscreen", "window": "--activewindow", "region": "--region"}
        if scope not in flags:
            return ActionResult("SCREENSHOT", False, "Choisis l'écran, la fenêtre active ou une zone.", error="INVALID_SCOPE")
        if not shutil.which("spectacle"):
            return ActionResult("SCREENSHOT", False, "Capture d'écran indisponible.", error="SCREENSHOT_UNAVAILABLE")
        try:
            self.destination.mkdir(parents=True, exist_ok=True)
            target = self.destination / f"capture_{scope}_{datetime.now():%Y%m%d_%H%M%S}_{uuid4().hex[:8]}.png"
            # Une instance séparée évite qu'une capture arrête une vidéo Spectacle.
            result = self.runner(["spectacle", "--new-instance", "-b", "-n", flags[scope], "-o", str(target)], check=False, capture_output=True, text=True, timeout=max(self.timeout, 60) if scope == "region" else self.timeout)
            if result.returncode != 0 or not target.is_file() or target.stat().st_size == 0:
                return ActionResult("SCREENSHOT", False, "La capture d'écran a échoué.", error="CAPTURE_FAILED")
            if self.announce_path:
                print(f"[CAPTURE] {target}", flush=True)
            return ActionResult("SCREENSHOT", True, "Capture enregistrée dans le dossier Pictures, Jarvis.", artifact_path=str(target))
        except subprocess.TimeoutExpired:
            return ActionResult("SCREENSHOT", False, "Capture annulée : le délai de sélection ou de capture est dépassé.", error="CAPTURE_TIMEOUT")
        except (OSError, subprocess.SubprocessError) as exc:
            return ActionResult("SCREENSHOT", False, "Capture d'écran indisponible.", error=str(exc))
