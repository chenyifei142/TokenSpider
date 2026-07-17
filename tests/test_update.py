import os
from pathlib import Path

os.environ["APPDATA"] = str(Path.cwd() / ".test-appdata")

import pytest
from unittest.mock import Mock, patch

from app_update import (
    GITHUB_LATEST_RELEASE_API_URL,
    _release_from_payload,
    _is_allowed_download_url,
    cleanup_pending_update,
    compare_versions,
    format_bytes,
    is_safe_cleanup_path,
    normalize_version,
    stable_target_path,
)


def test_semver_comparison_supports_prefix_and_prerelease():
    assert normalize_version("v1.1.9") == "1.1.9"
    assert normalize_version("1.2.0-beta.1") == "1.2.0-beta.1"
    assert compare_versions("1.2.0", "1.2.0") == 0
    assert compare_versions("1.1.9", "1.2.0") < 0
    assert compare_versions("1.2.0-beta.1", "1.2.0") < 0
    assert compare_versions("1.2.0", "1.2.0-beta.1") > 0


def test_release_asset_selection_prefers_tokenmeter_and_requires_updater():
    release = _release_from_payload(
        {
            "tag_name": "v1.3.0",
            "published_at": "2026-07-06T07:00:00Z",
            "body": "Bug fixes",
            "prerelease": False,
            "assets": [
                {
                    "name": "TokenScope-v1.3.0-windows-x64.exe",
                    "browser_download_url": "https://github.com/zensoku142/TokenMeter/releases/download/v1.3.0/TokenScope-v1.3.0-windows-x64.exe",
                    "size": 11,
                },
                {
                    "name": "TokenSpider-v1.3.0-windows-x64.exe",
                    "browser_download_url": "https://github.com/zensoku142/TokenMeter/releases/download/v1.3.0/TokenSpider-v1.3.0-windows-x64.exe",
                    "size": 10,
                },
                {
                    "name": "TokenMeter-v1.3.0-windows-x64.exe",
                    "browser_download_url": "https://github.com/zensoku142/TokenMeter/releases/download/v1.3.0/TokenMeter-v1.3.0-windows-x64.exe",
                    "size": 12,
                },
                {
                    "name": "TokenSpiderUpdater-v1.3.0-windows-x64.exe",
                    "browser_download_url": "https://github.com/zensoku142/TokenMeter/releases/download/v1.3.0/TokenSpiderUpdater-v1.3.0-windows-x64.exe",
                    "size": 5,
                },
                {
                    "name": "TokenMeterUpdater-v1.3.0-windows-x64.exe",
                    "browser_download_url": "https://github.com/zensoku142/TokenMeter/releases/download/v1.3.0/TokenMeterUpdater-v1.3.0-windows-x64.exe",
                    "size": 6,
                },
                {
                    "name": "SHA256SUMS.txt",
                    "browser_download_url": "https://github.com/zensoku142/TokenMeter/releases/download/v1.3.0/SHA256SUMS.txt",
                    "size": 2,
                },
            ],
        }
    )

    assert release.version == "1.3.0"
    assert release.app_asset.name == "TokenMeter-v1.3.0-windows-x64.exe"
    assert release.updater_asset.name == "TokenMeterUpdater-v1.3.0-windows-x64.exe"
    assert release.checksum_asset.name == "SHA256SUMS.txt"


def test_release_asset_selection_accepts_legacy_tokenscope_names():
    release = _release_from_payload(
        {
            "tag_name": "v1.3.0",
            "published_at": "2026-07-06T07:00:00Z",
            "body": "Bug fixes",
            "prerelease": False,
            "assets": [
                {
                    "name": "TokenScope-v1.3.0-windows-x64.exe",
                    "browser_download_url": "https://github.com/zensoku142/TokenMeter/releases/download/v1.3.0/TokenScope-v1.3.0-windows-x64.exe",
                    "size": 11,
                },
                {
                    "name": "TokenScopeUpdater-v1.3.0-windows-x64.exe",
                    "browser_download_url": "https://github.com/zensoku142/TokenMeter/releases/download/v1.3.0/TokenScopeUpdater-v1.3.0-windows-x64.exe",
                    "size": 5,
                },
                {
                    "name": "SHA256SUMS.txt",
                    "browser_download_url": "https://github.com/zensoku142/TokenMeter/releases/download/v1.3.0/SHA256SUMS.txt",
                    "size": 2,
                },
            ],
        }
    )

    assert release.app_asset.name == "TokenScope-v1.3.0-windows-x64.exe"
    assert release.updater_asset.name == "TokenScopeUpdater-v1.3.0-windows-x64.exe"


def test_release_asset_selection_accepts_legacy_tokenspider_names():
    release = _release_from_payload(
        {
            "tag_name": "v1.3.0",
            "assets": [
                {
                    "name": "TokenSpider-v1.3.0-windows-x64.exe",
                    "browser_download_url": "https://github.com/zensoku142/TokenMeter/releases/download/v1.3.0/TokenSpider-v1.3.0-windows-x64.exe",
                    "size": 10,
                },
                {
                    "name": "TokenSpiderUpdater-v1.3.0-windows-x64.exe",
                    "browser_download_url": "https://github.com/zensoku142/TokenMeter/releases/download/v1.3.0/TokenSpiderUpdater-v1.3.0-windows-x64.exe",
                    "size": 5,
                },
                {
                    "name": "SHA256SUMS.txt",
                    "browser_download_url": "https://github.com/zensoku142/TokenMeter/releases/download/v1.3.0/SHA256SUMS.txt",
                    "size": 2,
                },
            ],
        }
    )

    assert release.app_asset.name.startswith("TokenSpider-")
    assert release.updater_asset.name.startswith("TokenSpiderUpdater-")


@pytest.mark.parametrize("name", ["TokenMeter.exe", "TokenSpider.exe", "TokenScope.exe"])
def test_stable_target_path_preserves_existing_stable_shortcut_target(tmp_path, name):
    current = tmp_path / name
    assert stable_target_path(current) == current.resolve()


def test_stable_target_path_migrates_versioned_download_to_tokenmeter(tmp_path):
    current = tmp_path / "TokenSpider-v1.9.1-windows-x64.exe"
    assert stable_target_path(current) == (tmp_path / "TokenMeter.exe").resolve()


def test_update_urls_only_allow_new_repository_release_paths():
    assert GITHUB_LATEST_RELEASE_API_URL == (
        "https://api.github.com/repos/zensoku142/TokenMeter/releases/latest"
    )
    assert _is_allowed_download_url(
        "https://github.com/zensoku142/TokenMeter/releases/download/v2.0.0/TokenMeter.exe",
        require_release_path=True,
    )
    assert not _is_allowed_download_url(
        "https://github.com/zensoku142/TokenSpider/releases/download/v1.9.1/TokenSpider.exe",
        require_release_path=True,
    )


def test_format_bytes_uses_human_readable_units():
    assert format_bytes(0) == "未知"
    assert format_bytes(512) == "512 B"
    assert format_bytes(1024 * 1024) == "1.0 MB"


def _run_cleanup(tmp_path, cleanup_paths):
    updates = tmp_path / "updates"
    updates.mkdir(exist_ok=True)
    clear = Mock()
    with (
        patch("app_update.config_manager.load_pending_update_cleanup", return_value={
            "version": 1,
            "cleanup_paths": cleanup_paths,
        }),
        patch("app_update.config_manager.updates_dir", return_value=updates),
        patch("app_update.config_manager.clear_pending_update_cleanup", clear),
        patch("app_update.stable_target_path", return_value=tmp_path / "TokenSpider.exe"),
    ):
        cleanup_pending_update()
    clear.assert_called_once()
    return updates


def test_update_cleanup_removes_only_relative_cache_descendants(tmp_path):
    updates = tmp_path / "updates"
    child_dir = updates / "v2" / "nested"
    child_dir.mkdir(parents=True)
    child_file = updates / "old.exe"
    child_file.write_text("cache", encoding="utf-8")

    _run_cleanup(tmp_path, ["v2", "old.exe", "missing.exe"])

    assert not (updates / "v2").exists()
    assert not child_file.exists()


@pytest.mark.parametrize("unsafe", ["..\\outside.txt", ".", "\\", "C:\\"])
def test_update_cleanup_rejects_traversal_roots_and_absolute_paths(tmp_path, unsafe):
    outside = tmp_path / "outside.txt"
    outside.write_text("keep", encoding="utf-8")

    _run_cleanup(tmp_path, [unsafe, str(outside), str(Path.home())])

    assert outside.read_text(encoding="utf-8") == "keep"


def test_update_cleanup_rejects_symlink_resolving_to_outside(tmp_path):
    updates = tmp_path / "updates"
    updates.mkdir()
    outside = tmp_path / "outside"
    outside.mkdir()
    link = updates / "linked"
    original_resolve = Path.resolve
    resolved_link = original_resolve(link, strict=False)
    resolved_outside = original_resolve(outside, strict=False)

    def resolve_symlink(path, strict=False):
        resolved = original_resolve(path, strict=strict)
        return resolved_outside if resolved == resolved_link else resolved

    # Mocking resolve models both symbolic links and Windows directory junctions
    # without requiring elevated link-creation privileges in the test runner.
    with patch.object(Path, "resolve", new=resolve_symlink):
        assert not is_safe_cleanup_path(Path("linked"), updates)


def test_update_cleanup_ignores_and_clears_damaged_manifest(tmp_path):
    manifest = tmp_path / "pending-update-cleanup.json"
    manifest.write_text("{broken", encoding="utf-8")
    clear = Mock()
    with (
        patch("app_update.config_manager.load_pending_update_cleanup", return_value={}),
        patch("app_update.config_manager.PENDING_UPDATE_CLEANUP_PATH", manifest),
        patch("app_update.config_manager.clear_pending_update_cleanup", clear),
    ):
        cleanup_pending_update()
    clear.assert_called_once()
