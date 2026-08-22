"""Contrôle applicatif borné, sans shell arbitraire."""

from tools.applications import APPLICATIONS, open_application


def close_application(name):
    # La fermeture reste déclarative : elle est classée confirmation requise.
    if str(name).casefold().strip() not in APPLICATIONS:
        return False, "Application inconnue."
    return False, "La fermeture d'une application nécessite une confirmation explicite."


def is_application_running(name):
    return False  # détection volontairement conservative et portable


__all__ = ["open_application", "close_application", "is_application_running"]
