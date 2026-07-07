"""Standalone updater used to replace the running Windows executable."""

from __future__ import annotations

import argparse
import ctypes
import logging
import os
import shutil
import subprocess
import sys
import time
from pathlib import Path

from app_identity import APP_DISPLAY_NAME, APP_STORAGE_NAME


SYNCHRONIZE = 0x00100000
WAIT_OBJECT_0 = 0x00000000
WAIT_TIMEOUT = 0x00000102


def _default_log_path() -> Path:
    appdata = Path(os.environ.get("APPDATA", Path.home()))
    return appdata / APP_STORAGE_NAME / "TokenScopeUpdater.log"


def _build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description=f"{APP_DISPLAY_NAME} standalone updater")
    parser.add_argument("--wait-pid", type=int, required=True)
    parser.add_argument("--source", required=True)
    parser.add_argument("--target", required=True)
    parser.add_argument("--current-exe", required=True)
    parser.add_argument("--restart", action="store_true")
    parser.add_argument("--log-path", default=str(_default_log_path()))
    return parser


def _configure_logging(log_path: Path) -> logging.Logger:
    log_path.parent.mkdir(parents=True, exist_ok=True)
    logger = logging.getLogger("TokenScopeUpdater")
    logger.setLevel(logging.INFO)
    logger.handlers.clear()
    handler = logging.FileHandler(log_path, encoding="utf-8")
    handler.setFormatter(logging.Formatter("%(asctime)s [%(levelname)s] %(message)s"))
    logger.addHandler(handler)
    logger.propagate = False
    return logger


def _wait_for_process_exit(pid: int, logger: logging.Logger, timeout_seconds: int = 120) -> None:
    kernel32 = ctypes.WinDLL("kernel32", use_last_error=True)
    process = kernel32.OpenProcess(SYNCHRONIZE, False, pid)
    if not process:
        logger.info("Process %s already exited", pid)
        return
    try:
        result = kernel32.WaitForSingleObject(process, timeout_seconds * 1000)
        if result == WAIT_OBJECT_0:
            logger.info("Process %s exited", pid)
            return
        if result == WAIT_TIMEOUT:
            raise TimeoutError(f"Timed out waiting for process {pid} to exit")
        raise OSError(f"WaitForSingleObject failed with code {result}")
    finally:
        kernel32.CloseHandle(process)


def _copy_source_into_target_dir(source: Path, target: Path, logger: logging.Logger) -> Path:
    stage_path = target.with_suffix(target.suffix + ".new")
    stage_path.unlink(missing_ok=True)
    logger.info("Copying %s to %s", source, stage_path)
    shutil.copy2(source, stage_path)
    return stage_path


def _replace_install(
    source: Path,
    target: Path,
    current_exe: Path,
    logger: logging.Logger,
) -> tuple[Path | None, Path | None]:
    target.parent.mkdir(parents=True, exist_ok=True)
    stage_path = _copy_source_into_target_dir(source, target, logger)
    backup_source = target if target.exists() else current_exe
    backup_path: Path | None = None
    restore_path: Path | None = None
    if backup_source.exists():
        backup_path = backup_source.with_suffix(backup_source.suffix + ".bak")
        backup_path.unlink(missing_ok=True)
        restore_path = backup_source
        logger.info("Backing up %s to %s", backup_source, backup_path)
        os.replace(backup_source, backup_path)
    try:
        logger.info("Replacing %s with %s", target, stage_path)
        os.replace(stage_path, target)
    except Exception:
        stage_path.unlink(missing_ok=True)
        if backup_path and restore_path and backup_path.exists():
            os.replace(backup_path, restore_path)
        raise
    return backup_path, restore_path


def _restart_target(target: Path, logger: logging.Logger) -> None:
    creation_flags = getattr(subprocess, "CREATE_NO_WINDOW", 0)
    logger.info("Restarting %s", target)
    process = subprocess.Popen([str(target)], creationflags=creation_flags, close_fds=False)
    time.sleep(3)
    if process.poll() not in (None, 0):
        raise RuntimeError(f"Restarted process exited immediately with code {process.poll()}")


def _restore_backup(
    target: Path,
    backup_path: Path | None,
    restore_path: Path | None,
    logger: logging.Logger,
) -> None:
    if backup_path is None or restore_path is None or not backup_path.exists():
        return
    logger.warning("Restoring backup from %s", backup_path)
    target.unlink(missing_ok=True)
    os.replace(backup_path, restore_path)


def main(argv: list[str] | None = None) -> int:
    args = _build_parser().parse_args(argv)
    logger = _configure_logging(Path(args.log_path))
    source = Path(args.source).resolve()
    target = Path(args.target).resolve()
    current_exe = Path(args.current_exe).resolve()
    if not source.exists():
        logger.error("Source executable missing: %s", source)
        return 1
    try:
        _wait_for_process_exit(args.wait_pid, logger)
        backup_path, restore_path = _replace_install(source, target, current_exe, logger)
        if args.restart:
            try:
                _restart_target(target, logger)
            except Exception:
                _restore_backup(target, backup_path, restore_path, logger)
                raise
        logger.info("Update completed successfully")
        return 0
    except Exception as exc:
        logger.exception("Update failed: %s", exc)
        return 1


if __name__ == "__main__":
    raise SystemExit(main())
