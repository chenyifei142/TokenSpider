"""Shared application identity and release metadata."""

from __future__ import annotations

APP_DISPLAY_NAME = "TokenMeter"
APP_STORAGE_NAME = "TokenSpider"
APP_VERSION = "1.9.1"

# Keep the legacy storage and mutex identities so upgrades retain user data,
# credentials, and single-instance coordination across every public rename.
SINGLE_INSTANCE_MUTEX = "Local\\TokenSpider.SingleInstance"

MAIN_EXECUTABLE_NAME = "TokenMeter.exe"
UPDATER_EXECUTABLE_NAME = "TokenMeterUpdater.exe"
MAIN_RELEASE_ASSET_TEMPLATE = "TokenMeter-v{version}-windows-x64.exe"
LEGACY_MAIN_RELEASE_ASSET_TEMPLATES = (
    "TokenSpider-v{version}-windows-x64.exe",
    "TokenScope-v{version}-windows-x64.exe",
)
UPDATER_RELEASE_ASSET_TEMPLATE = "TokenMeterUpdater-v{version}-windows-x64.exe"
LEGACY_UPDATER_RELEASE_ASSET_TEMPLATES = (
    "TokenSpiderUpdater-v{version}-windows-x64.exe",
    "TokenScopeUpdater-v{version}-windows-x64.exe",
)
SHA256_RELEASE_ASSET_NAME = "SHA256SUMS.txt"

GITHUB_REPOSITORY = "zensoku142/TokenMeter"
GITHUB_RELEASES_URL = f"https://github.com/{GITHUB_REPOSITORY}/releases"
GITHUB_RELEASES_API_URL = f"https://api.github.com/repos/{GITHUB_REPOSITORY}/releases"
GITHUB_LATEST_RELEASE_API_URL = f"{GITHUB_RELEASES_API_URL}/latest"
