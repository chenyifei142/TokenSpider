import ast
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]


def _call_keywords(path: str, name: str) -> dict[str, object]:
    tree = ast.parse((ROOT / path).read_text(encoding="utf-8"))
    for node in ast.walk(tree):
        if not isinstance(node, ast.Call):
            continue
        if isinstance(node.func, ast.Name) and node.func.id == name:
            return {
                keyword.arg: ast.literal_eval(keyword.value)
                for keyword in node.keywords
                if keyword.arg is not None
            }
    raise AssertionError(f"{name} call not found in {path}")


def test_pyqtgraph_startup_modules_are_packaged():
    options = _call_keywords("TokenSpider.spec", "Analysis")
    excluded = set(options["excludes"])
    required = {
        "pyqtgraph.imageview",
        "pyqtgraph.multiprocess",
        "pyqtgraph.parametertree",
    }

    assert required.isdisjoint(excluded)
    assert {
        "PySide6.QtOpenGL",
        "PySide6.QtOpenGLWidgets",
    } <= set(options["hiddenimports"])


def test_main_executable_uses_stable_name_and_project_icon():
    options = _call_keywords("TokenSpider.spec", "EXE")

    assert options["name"] == "TokenScope"
    assert options["icon"] == ["assets/TokenSpider.ico"]


def test_updater_executable_is_packaged_separately():
    options = _call_keywords("TokenScopeUpdater.spec", "EXE")

    assert options["name"] == "TokenScopeUpdater"
    assert options["icon"] == ["assets/TokenSpider.ico"]
