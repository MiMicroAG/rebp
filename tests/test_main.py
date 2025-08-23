import importlib.util
from pathlib import Path

# テスト実行時にプロジェクトルートの main.py を明示的に読み込む
project_root = Path(__file__).resolve().parent.parent
main_path = project_root / "main.py"
spec = importlib.util.spec_from_file_location("main", str(main_path))
assert spec is not None and spec.loader is not None, f"Failed to load spec for {main_path}"
main_mod = importlib.util.module_from_spec(spec)  # type: ignore[arg-type]
spec.loader.exec_module(main_mod)  # type: ignore[attr-defined]


def test_main_default():
    # main([]) は正常終了コード 0 を返すことを期待
    assert main_mod.main([]) == 0
