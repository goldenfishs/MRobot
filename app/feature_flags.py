from __future__ import annotations

from PyQt5.QtCore import QSettings


AI_BETA_KEY = "features/aiBetaEnabled"


def is_ai_beta_enabled(settings: QSettings | None = None) -> bool:
    store = settings or QSettings("MRobot", "MRobot")
    return store.value(AI_BETA_KEY, False, type=bool)


def set_ai_beta_enabled(enabled: bool, settings: QSettings | None = None) -> None:
    store = settings or QSettings("MRobot", "MRobot")
    store.setValue(AI_BETA_KEY, bool(enabled))
    store.sync()
