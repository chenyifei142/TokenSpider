from unittest.mock import patch

import main


def test_second_instance_exits_before_runtime_initialization():
    with (
        patch.object(main, "_acquire_single_instance", return_value=None),
        patch.object(main.config_manager, "initialize") as initialize,
        patch.object(main.ctypes, "windll", create=True),
    ):
        assert main.main() == 0

    initialize.assert_not_called()
