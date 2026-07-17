"""Build release artifacts for GitHub Releases."""

from __future__ import annotations

import argparse
import hashlib
import shutil
import subprocess
import sys
import time
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from app_identity import (
    APP_VERSION,
    MAIN_EXECUTABLE_NAME,
    MAIN_RELEASE_ASSET_TEMPLATE,
    UPDATER_EXECUTABLE_NAME,
    UPDATER_RELEASE_ASSET_TEMPLATE,
)

DIST_DIR = ROOT / "dist"
MAIN_SPEC = ROOT / "TokenMeter.spec"
UPDATER_SPEC = ROOT / "TokenMeterUpdater.spec"
SHA_FILE = DIST_DIR / "SHA256SUMS.txt"


def _run(command: list[str]) -> None:
    subprocess.run(command, cwd=ROOT, check=True)


def _sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def _copy_release_asset(source: Path, template: str) -> Path:
    target = DIST_DIR / template.format(version=APP_VERSION)
    shutil.copy2(source, target)
    return target


def _write_sha256_file(paths: list[Path]) -> None:
    lines = [f"{_sha256(path)} *{path.name}" for path in paths]
    SHA_FILE.write_text("\n".join(lines) + "\n", encoding="utf-8")


def _smoke_test_main(executable: Path) -> None:
    process = subprocess.Popen([str(executable)], cwd=executable.parent)
    try:
        time.sleep(5)
        if process.poll() not in (None, 0):
            raise RuntimeError(f"{executable.name} exited early with code {process.poll()}")
    finally:
        if process.poll() is None:
            process.terminate()
            process.wait(timeout=10)


def _smoke_test_updater(executable: Path) -> None:
    subprocess.run([str(executable), "--help"], cwd=executable.parent, check=True)


def build_release(*, skip_smoke_test: bool) -> None:
    DIST_DIR.mkdir(parents=True, exist_ok=True)
    _run([sys.executable, "-m", "PyInstaller", "--clean", "--noconfirm", str(MAIN_SPEC)])
    _run([sys.executable, "-m", "PyInstaller", "--clean", "--noconfirm", str(UPDATER_SPEC)])

    # Reuse the identity constants so build outputs and release asset names stay
    # aligned after repository/branding adjustments.
    main_exe = DIST_DIR / MAIN_EXECUTABLE_NAME
    updater_exe = DIST_DIR / UPDATER_EXECUTABLE_NAME
    if not main_exe.exists() or not updater_exe.exists():
        raise FileNotFoundError("PyInstaller did not produce both executables")

    main_release = _copy_release_asset(main_exe, MAIN_RELEASE_ASSET_TEMPLATE)
    updater_release = _copy_release_asset(updater_exe, UPDATER_RELEASE_ASSET_TEMPLATE)
    _write_sha256_file([main_release, updater_release])

    if not skip_smoke_test:
        _smoke_test_updater(updater_exe)
        _smoke_test_main(main_exe)


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="Build TokenMeter release assets")
    parser.add_argument("--skip-smoke-test", action="store_true")
    args = parser.parse_args(argv)
    build_release(skip_smoke_test=args.skip_smoke_test)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
