"""Compatibility helpers backed by the shared update service."""

from __future__ import annotations

from typing import Optional

from app.update_service import DEFAULT_REPOSITORY, UpdateService


def check_update(local_version: str, repo: str = DEFAULT_REPOSITORY) -> str | None:
    update = UpdateService(local_version, repo).check()
    return update.version if update else None


def check_update_availability(
    current_version: str, repo: str = DEFAULT_REPOSITORY
) -> Optional[dict[str, object]]:
    update = UpdateService(current_version, repo).check()
    return update.to_dict() if update else None
