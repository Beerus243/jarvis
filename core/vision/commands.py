"""Reconnaissance locale des demandes de vision, avant le fallback texte."""
from dataclasses import dataclass
import re

from core.command_understanding import normalize_command


@dataclass(frozen=True)
class VisionRequest:
    source: str
    question: str


def parse_vision_request(message):
    text = normalize_command(message)
    text = re.sub(r'^(?:hey )?jarvis ', '', text)
    screen = (
        r'(?:regarde|analyse|decris|observe) (?:mon|l|cet) ecran',
        r'(?:lis|resume) (?:le texte|ce qui est affiche) (?:sur|a) (?:mon|l) ecran',
        r'(?:explique|analyse) (?:l|cette) erreur (?:sur|a) (?:mon|l) ecran',
        r'(?:que vois tu|qu est ce que tu vois) (?:sur|a) (?:mon|l) ecran',
    )
    webcam = (
        r'(?:regarde|analyse|decris|observe) (?:avec|via) (?:ma|la) (?:webcam|camera)',
        r'(?:que vois tu|qu est ce que tu vois) (?:avec|via|devant) (?:ma|la) (?:webcam|camera)',
        r'(?:regarde|decris) (?:ce qui est )?devant (?:ma|la) (?:webcam|camera)',
    )
    for source, patterns in (('screen', screen), ('webcam', webcam)):
        if any(re.match('^' + pattern + r'(?:\s|$)', text) for pattern in patterns):
            return VisionRequest(source, str(message).strip())
    return None


def handle_vision_command(message):
    from core.vision.watch_commands import handle_watch_command
    watched = handle_watch_command(message)
    if watched is not None:
        return watched
    text = re.sub(r'^(?:hey )?jarvis ', '', normalize_command(message))
    if text in {'oublie ce que tu as vu', 'oublie la derniere image', 'efface le contexte visuel'}:
        from core.vision.context import visual_session
        visual_session.clear()
        from core.runtime import get_runtime
        runtime = get_runtime()
        if runtime and runtime.visual_watch.snapshot():
            runtime.visual_watch.stop()
            return 'Le contexte visuel temporaire est effacé et la surveillance est arrêtée.'
        return 'Le contexte visuel temporaire est effacé.'
    request = parse_vision_request(message)
    if request is not None:
        from core.vision.service import analyze_request
        return analyze_request(request)
    if text in {'regarde a nouveau', 'regarde encore', 'actualise la vue', 'reprends une image'}:
        from core.vision.service import followup
        return followup(str(message).strip(), refresh=True)
    patterns = (
        r'(?:explique|detaille|analyse) (?:cette erreur|ce message|ce que tu vois)',
        r'(?:lis|resume|traduis) (?:ce texte|ce passage|le texte de l image)',
        r'(?:decris|identifie) (?:cet objet|cet element)',
        r'(?:que signifie|c est quoi) (?:cette erreur|ce message|cet objet)',
    )
    if any(re.match('^' + pattern + r'(?:\s|$)', text) for pattern in patterns):
        from core.vision.service import followup
        from core.vision.context import visual_session
        # Sans contexte, une question générale doit conserver son routage.
        if visual_session.get() is not None:
            return followup(str(message).strip())
        if any(re.fullmatch(pattern, text) for pattern in patterns):
            from core.vision.service import NO_CONTEXT
            return NO_CONTEXT
    return None
