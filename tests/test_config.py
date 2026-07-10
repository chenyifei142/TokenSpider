import json
import os
import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch

os.environ["APPDATA"] = str(Path.cwd() / ".test-appdata")

import config_manager


class ConfigTests(unittest.TestCase):
    def test_boolean_and_provider_values_are_validated(self):
        self.assertFalse(
            config_manager.validate_config({"EDGE_HIDE_ENABLED": "false"})[
                "EDGE_HIDE_ENABLED"
            ]
        )
        self.assertTrue(
            config_manager.validate_config({})[
                "PANEL_AUTO_COLLAPSE_ON_DEACTIVATE"
            ]
        )
        self.assertFalse(
            config_manager.validate_config(
                {"PANEL_AUTO_COLLAPSE_ON_DEACTIVATE": "false"}
            )["PANEL_AUTO_COLLAPSE_ON_DEACTIVATE"]
        )
        self.assertEqual(
            config_manager.validate_config({"UPDATE_CHANNEL": "prerelease"})["UPDATE_CHANNEL"],
            "prerelease",
        )
        with self.assertRaises(ValueError):
            config_manager.validate_config({"ACTIVE_PROVIDER": "unknown"})
        with self.assertRaises(ValueError):
            config_manager.validate_config({"UPDATE_CHANNEL": "nightly"})

    def test_legacy_default_compact_size_is_migrated(self):
        temp_root = Path.cwd() / ".test-appdata" / "tmp"
        temp_root.mkdir(parents=True, exist_ok=True)
        with tempfile.TemporaryDirectory(dir=temp_root) as directory:
            config_path = Path(directory) / "config.json"
            config_path.write_text(
                json.dumps({"WIDGET_COMPACT_SIZE": 120}), encoding="utf-8"
            )
            with patch.object(config_manager, "CONFIG_PATH", config_path):
                values = config_manager._load_public_config()

            self.assertEqual(values["WIDGET_COMPACT_SIZE"], 96)

            config_path.write_text(
                json.dumps({"WIDGET_COMPACT_SIZE": 108}), encoding="utf-8"
            )
            with patch.object(config_manager, "CONFIG_PATH", config_path):
                previous_values = config_manager._load_public_config()

            self.assertEqual(previous_values["WIDGET_COMPACT_SIZE"], 96)

            config_path.write_text(
                json.dumps({"WIDGET_COMPACT_SIZE": 112}), encoding="utf-8"
            )
            with patch.object(config_manager, "CONFIG_PATH", config_path):
                custom_values = config_manager._load_public_config()

            self.assertEqual(custom_values["WIDGET_COMPACT_SIZE"], 112)

    def test_panel_auto_collapse_setting_round_trips(self):
        temp_root = Path.cwd() / ".test-appdata" / "tmp"
        temp_root.mkdir(parents=True, exist_ok=True)
        with tempfile.TemporaryDirectory(dir=temp_root) as directory:
            root = Path(directory)
            config_path = root / "config.json"
            config_path.write_text(
                json.dumps(config_manager._public_values(config_manager.DEFAULT_CONFIG)),
                encoding="utf-8",
            )
            old_config = config_manager._config
            try:
                with (
                    patch.object(config_manager, "CONFIG_DIR", root),
                    patch.object(config_manager, "CONFIG_PATH", config_path),
                    patch.object(config_manager, "_write_credential"),
                    patch.object(config_manager, "_read_credential", return_value=""),
                ):
                    config_manager._config = config_manager.DEFAULT_CONFIG.copy()
                    saved = config_manager.save_config(
                        {"PANEL_AUTO_COLLAPSE_ON_DEACTIVATE": False}
                    )
                    loaded = config_manager.load_config()

                self.assertFalse(saved["PANEL_AUTO_COLLAPSE_ON_DEACTIVATE"])
                self.assertFalse(loaded["PANEL_AUTO_COLLAPSE_ON_DEACTIVATE"])
            finally:
                config_manager._config = old_config

    def test_backups_exclude_secrets_and_are_limited(self):
        temp_root = Path.cwd() / ".test-appdata" / "tmp"
        temp_root.mkdir(parents=True, exist_ok=True)
        with tempfile.TemporaryDirectory(dir=temp_root) as directory:
            root = Path(directory)
            config_path = root / "config.json"
            old_config = config_manager._config
            values = config_manager.validate_config({
                "DEEPSEEK_API_KEY": "secret-api-key",
                "DEEPSEEK_AUTH": "secret-auth",
                "DEEPSEEK_COOKIE": "secret-cookie",
            })
            public = config_manager._public_values(values)
            config_path.write_text(json.dumps(public), encoding="utf-8")
            try:
                with (
                    patch.object(config_manager, "CONFIG_DIR", root),
                    patch.object(config_manager, "CONFIG_PATH", config_path),
                    patch.object(config_manager, "_config", values),
                    patch.object(config_manager, "_write_credential"),
                ):
                    for interval in range(5):
                        config_manager.save_config({"REFRESH_INTERVAL": 60_000 + interval})
                    files = list(root.glob("config.json.bak-*"))
                    self.assertEqual(len(files), 3)
                    content = "\n".join(path.read_text(encoding="utf-8") for path in files)
                    self.assertNotIn("secret-api-key", content)
                    self.assertNotIn("secret-auth", content)
                    self.assertNotIn("secret-cookie", content)
            finally:
                config_manager._config = old_config

    def test_panel_layout_state_round_trips_separately(self):
        temp_root = Path.cwd() / ".test-appdata" / "tmp"
        temp_root.mkdir(parents=True, exist_ok=True)
        with tempfile.TemporaryDirectory(dir=temp_root) as directory:
            layout_path = Path(directory) / "panel-layout.json"
            payload = {
                "sections": ["bottom", "top", "middle"],
                "top_cards": ["month", "today", "balance"],
                "bottom_cards": ["statistics", "trend"],
            }

            with patch.object(config_manager, "PANEL_LAYOUT_PATH", layout_path):
                config_manager.save_panel_layout_state(payload)
                self.assertEqual(config_manager.load_panel_layout_state(), payload)

                layout_path.write_text("[]", encoding="utf-8")
                self.assertEqual(config_manager.load_panel_layout_state(), {})

    def test_update_state_round_trips_separately(self):
        temp_root = Path.cwd() / ".test-appdata" / "tmp"
        temp_root.mkdir(parents=True, exist_ok=True)
        with tempfile.TemporaryDirectory(dir=temp_root) as directory:
            state_path = Path(directory) / "update-state.json"
            cleanup_path = Path(directory) / "pending-update-cleanup.json"
            payload = {"latest_version": "1.3.0", "last_checked_at": "2026-07-06T00:00:00+00:00"}
            cleanup_payload = {"version": 1, "cleanup_paths": ["C:/tmp/demo"]}

            with (
                patch.object(config_manager, "UPDATE_STATE_PATH", state_path),
                patch.object(config_manager, "PENDING_UPDATE_CLEANUP_PATH", cleanup_path),
            ):
                config_manager.save_update_state(payload)
                self.assertEqual(config_manager.load_update_state(), payload)
                config_manager.save_pending_update_cleanup(cleanup_payload)
                self.assertEqual(config_manager.load_pending_update_cleanup(), cleanup_payload)
                config_manager.clear_pending_update_cleanup()
                self.assertEqual(config_manager.load_pending_update_cleanup(), {})


if __name__ == "__main__":
    unittest.main()
