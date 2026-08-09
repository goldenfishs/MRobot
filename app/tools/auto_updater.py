"""Qt adapter for the platform-neutral MRobot update service."""

from __future__ import annotations

from typing import Optional

from PyQt5.QtCore import QObject, QThread, pyqtSignal

from app.update_service import DEFAULT_REPOSITORY, InstallPlan, UpdateInfo, UpdateService


class UpdaterSignals(QObject):
    progress_changed = pyqtSignal(int)
    download_progress = pyqtSignal(int, int, float, float)
    status_changed = pyqtSignal(str)
    error_occurred = pyqtSignal(str)
    install_ready = pyqtSignal(object)
    update_cancelled = pyqtSignal()


class AutoUpdater(QThread):
    """Download, verify and prepare an update without blocking the GUI."""

    def __init__(
        self,
        current_version: str,
        repo: str = DEFAULT_REPOSITORY,
        update_info: UpdateInfo | None = None,
    ) -> None:
        super().__init__()
        self.signals = UpdaterSignals()
        self.service = UpdateService(current_version, repo)
        self.update_info = update_info
        self.cancelled = False

    def cancel_update(self) -> None:
        self.cancelled = True

    def check_for_updates(self) -> Optional[dict[str, object]]:
        update = self.service.check()
        return update.to_dict() if update else None

    def _progress(self, downloaded: int, total: int) -> None:
        if self.cancelled:
            raise InterruptedError("更新已取消")
        percent = int(downloaded * 90 / total) if total else 0
        self.signals.progress_changed.emit(min(percent, 90))
        self.signals.download_progress.emit(downloaded, total, 0.0, 0.0)

    def run(self) -> None:
        try:
            self.signals.status_changed.emit("正在检查更新…")
            info = self.update_info or self.service.check()
            if info is None:
                self.signals.status_changed.emit("当前已是最新版本")
                return
            if self.cancelled:
                raise InterruptedError("更新已取消")
            if not self.service.frozen:
                raise RuntimeError("源码运行模式不会自动覆盖自身，请通过 Git 更新源码")
            self.signals.status_changed.emit(f"正在下载 MRobot {info.version}…")
            downloaded = self.service.download(info, self._progress)
            self.signals.progress_changed.emit(92)
            self.signals.status_changed.emit("SHA-256 校验通过，正在准备安装…")
            plan = self.service.prepare_install(downloaded)
            self.signals.progress_changed.emit(100)
            self.signals.status_changed.emit("更新已就绪，即将安装并重新启动…")
            self.signals.install_ready.emit(plan)
        except InterruptedError:
            self.signals.update_cancelled.emit()
        except Exception as exc:
            self.signals.error_occurred.emit(str(exc))

    def launch_install(self, plan: InstallPlan) -> None:
        self.service.launch_install(plan)


def check_update_availability(
    current_version: str, repo: str = DEFAULT_REPOSITORY
) -> Optional[dict[str, object]]:
    update = UpdateService(current_version, repo).check()
    return update.to_dict() if update else None
