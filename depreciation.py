import os
import csv
from typing import Dict, List, Any, Optional
from utils import to_float, to_int  # type: ignore

try:
    import yaml  # type: ignore
except ImportError:
    yaml = None


def _compute_used_life(statutory_life: int, elapsed: int) -> int:
    """
    中古耐用年数の算出（添付スクリーンショットのルールに準拠）

    ルール（この実装での仮定）:
    - 経過年数 < 法定耐用年数 の場合:
        中古耐用年数 = (法定耐用年数 - 経過年数) + round(経過年数 * 0.2)
      （経過年数 * 0.2 の端数は四捨五入で整数化）
    - 経過年数 >= 法定耐用年数 の場合:
        中古耐用年数 = max(1, round(法定耐用年数 * 0.2))

    注意: 税法上の端数処理の正確なルールが不明なため、ここでは四捨五入で実装しています。
    必要なら端数処理（切り上げ/切り捨て）を切替可能にします。
    """
    if elapsed < 0:
        raise ValueError("elapsed must be >= 0")
    if statutory_life <= 0:
        raise ValueError("statutory_life must be > 0")

    if elapsed < statutory_life:
        extra = int(round(elapsed * 0.2))
        used = (statutory_life - elapsed) + extra
    else:
        used = max(1, int(round(statutory_life * 0.2)))

    return int(used)


_RATES_CACHE: Dict[int, float] = {}


def _load_straight_line_rates_csv(path: str) -> Dict[int, float]:
    rates: Dict[int, float] = {}
    with open(path, newline="", encoding="utf-8") as f:
        reader = csv.DictReader((row for row in f if not row.strip().startswith('#')))
        for row in reader:
            try:
                life = int(row["service_life"])  # 償却年数
                rate = float(row["straight_line_rate"])  # 定額法償却率
                # 小数第3位丸め（表は既に丸め済だがコードの一貫性のため）
                rates[life] = round(rate, 3)
            except Exception:
                continue
    return rates


def _get_rates_table() -> Dict[int, float]:
    global _RATES_CACHE
    if _RATES_CACHE:
        return _RATES_CACHE
    # 優先: 環境変数で明示（DEPRECIATION_RATES_CSV）
    env_path = os.getenv("DEPRECIATION_RATES_CSV")
    search_paths: List[str] = []
    if env_path:
        search_paths.append(env_path)
    here = os.path.dirname(__file__)
    # 既定のCSVパス（プロジェクト内 data/ と examples/ の順）
    search_paths.append(os.path.join(here, "data", "depreciation_rates_jpn.csv"))
    search_paths.append(os.path.join(here, "examples", "depreciation_rates_jpn.csv"))

    for p in search_paths:
        if p and os.path.exists(p):
            _RATES_CACHE = _load_straight_line_rates_csv(p)
            break
    else:
        _RATES_CACHE = {}
    return _RATES_CACHE


def _rate_for_used_life(used_life: int) -> float:
    """
    定額法の年率を返す。優先: 公式表の率 -> フォールバック: 1/used_life を小数第3位丸め。
    """
    if used_life <= 0:
        raise ValueError("used_life must be > 0")
    table = _get_rates_table()
    if used_life in table:
        return float(table[used_life])
    return round(1.0 / used_life, 3)


def compute_depreciation(
    building_cost: float,
    equipment_cost: float,
    elapsed_years: int,
    building_statutory_life: int = 34,
    equipment_statutory_life: int = 15,
    round_to_yen: bool = True,
) -> Dict[str, Any]:
    """
    建物本体と付属設備それぞれの年単位の減価償却費を計算して返す。

    返り値の構造:
    {
      'building': {
         'statutory_life': int,
         'elapsed_years': int,
         'used_life': int,
         'rate': float,
         'annual_depreciation': [amount, ...],
         'total': float
      },
      'equipment': { ... }
    }

    annual_depreciation は長さがそれぞれの中古耐用年数になります。
    round_to_yen=True の時は各年の額を円で四捨五入して整数で返します。
    """
    if building_cost < 0 or equipment_cost < 0:
        raise ValueError("Costs must be non-negative")

    b_used = _compute_used_life(building_statutory_life, elapsed_years)
    e_used = _compute_used_life(equipment_statutory_life, elapsed_years)

    b_rate = _rate_for_used_life(b_used)
    e_rate = _rate_for_used_life(e_used)

    def _make_schedule(cost: float, rate: float, years: int) -> List[float]:
        """従来の単純な定額（丸め）スケジュール。"""
        annual = cost * rate
        if round_to_yen:
            amt = int(round(annual))
            return [amt for _ in range(years)]
        else:
            return [annual for _ in range(years)]

    def _make_last_year_adjusted_schedule(cost: float, rate: float, years: int, residual_yen: int = 1) -> List[int]:
        """
        各年は定額（丸め）とし、最後の年のみ調整して残存簿価 residual_yen を確保する。
        cost が 0 または residual_yen 以下の場合は全期間 0 を返す。
        """
        if years <= 0:
            return []
        cost_yen = int(round(cost))
        if cost_yen <= int(residual_yen):
            return [0 for _ in range(years)]
        target = cost_yen - int(residual_yen)
        if years == 1:
            return [int(target)]
        # 先行年の金額は丸めた年額を基本としつつ、合計が target を超えないよう上限を設ける
        base = int(round(cost * rate))
        max_base = target // (years - 1)
        base = min(base, max_base)
        schedule = [base for _ in range(years - 1)]
        last = int(target - base * (years - 1))
        return schedule + [last]

    if round_to_yen:
        # 建物・設備とも、最後の年のみで1円残るよう調整
        b_schedule = _make_last_year_adjusted_schedule(building_cost, b_rate, b_used, residual_yen=1)
        e_schedule = _make_last_year_adjusted_schedule(equipment_cost, e_rate, e_used, residual_yen=1)
    else:
        b_schedule = _make_schedule(building_cost, b_rate, b_used)
        e_schedule = _make_schedule(equipment_cost, e_rate, e_used)

    return {
        "building": {
            "statutory_life": int(building_statutory_life),
            "elapsed_years": int(elapsed_years),
            "used_life": int(b_used),
            "rate": float(b_rate),
            "annual_depreciation": b_schedule,
            "total": sum(b_schedule),
        },
        "equipment": {
            "statutory_life": int(equipment_statutory_life),
            "elapsed_years": int(elapsed_years),
            "used_life": int(e_used),
            "rate": float(e_rate),
            "annual_depreciation": e_schedule,
            "total": sum(e_schedule),
        },
    }


def _find_project_config() -> str:
    """プロジェクトルート上の project_config.yml を探索してパスを返す（見つからなければ空文字）。"""
    from pathlib import Path

    here = Path(__file__).resolve().parent
    # 5階層上まで探索
    for _ in range(6):
        candidate = here / "project_config.yml"
        if candidate.exists():
            return str(candidate)
        if here.parent == here:
            break
        here = here.parent
    return ""


def compute_depreciation_from_config(yaml_path: Optional[str] = None) -> Dict[str, Any]:
    """
    YAML設定ファイルからパラメータを読み取り、compute_depreciation を実行して返す。

    - yaml_path を与えればそのファイルを読む。
    - yaml_path が None の場合はリポジトリルートの `project_config.yml` を探し、それを利用する。

    期待する YAML フォーマット（例）:

    elapsed_years: 15
    building:
      cost: 35654400
      statutory_life: 34
    equipment:
      cost: 1234567
      statutory_life: 15

    statutory_life は省略可能（デフォルト 34 / 15 を使用）。
    """
    if yaml is None:
        raise RuntimeError("PyYAML is required to load config YAML (install pyyaml)")

    if yaml_path is None:
        yaml_path = _find_project_config()
        if not yaml_path:
            raise FileNotFoundError("project_config.yml not found in project tree; provide yaml_path")

    if not os.path.exists(yaml_path):
        raise FileNotFoundError(yaml_path)

    with open(yaml_path, "r", encoding="utf-8") as fh:
        cfg = yaml.safe_load(fh) or {}

    elapsed = to_int(cfg.get("elapsed_years", 0))
    b_cfg = cfg.get("building", {}) or {}
    e_cfg = cfg.get("equipment", {}) or {}

    b_cost = to_float(b_cfg.get("cost", 0))
    # If equipment cost is not provided (or set to 0), treat it as unspecified and
    # split building cost: building 85% / equipment 15%.
    raw_e_cost = e_cfg.get("cost", None)
    if raw_e_cost is None or to_float(raw_e_cost) == 0.0:
        # split
        e_cost = b_cost * 0.15
        b_cost = b_cost * 0.85
    else:
        e_cost = to_float(raw_e_cost)
    b_stat = to_int(b_cfg.get("statutory_life", 34))
    e_stat = to_int(e_cfg.get("statutory_life", 15))

    return compute_depreciation(
        building_cost=b_cost,
        equipment_cost=e_cost,
        elapsed_years=elapsed,
        building_statutory_life=b_stat,
        equipment_statutory_life=e_stat,
        round_to_yen=True,
    )
