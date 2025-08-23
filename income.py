from typing import List, Dict, Any, Optional
from utils import to_float, to_int  # type: ignore
import os

try:
    import yaml  # type: ignore
except ImportError:
    yaml = None


def _extend_to_years(vals: List[float], years: int) -> List[float]:
    if not vals:
        return [0.0] * years
    if len(vals) >= years:
        return vals[:years]
    last = vals[-1]
    return vals + [last] * (years - len(vals))


def _coerce_rates(value: Any, years: int, default: float = 0.0) -> List[float]:
    # Accept scalar or list; None -> default
    if value is None:
        return [default] * years
    if isinstance(value, (int, float)):
        return [float(value)] * years
    if isinstance(value, list):
        out: List[float] = []
        for v in value:
            try:
                out.append(float(v))
            except Exception:
                out.append(default)
        return _extend_to_years(out, years)
    # otherwise fallback
    return [default] * years


def _gen_trend_series(initial: float, growth: float, years: int) -> List[float]:
    """
    初期値 initial から始め、毎年 growth だけ相対的に増減する系列を作る。
    例: initial=0.05, growth=0.1 -> 0.05, 0.055, 0.0605, ...
    """
    seq: List[float] = []
    val = float(initial)
    for _ in range(years):
        seq.append(val)
        val = val * (1.0 + float(growth))
    return seq


def compute_income(
    monthly_rent: float,
    units: int = 1,
    years: int = 40,
    rent_change_rates: Optional[List[float]] = None,
    vacancy_rates: Optional[List[float]] = None,
    round_to_yen: bool = True,
) -> List[Dict[str, Any]]:
    """
    年次の賃料収入を40年（years可変）分計算して返す。

    - monthly_rent: 初年度の1戸あたり月額賃料（円）
    - units: 戸数（収入は monthly_rent × units × 12 から空室率控除）
    - rent_change_rates: 各年の賃料変動率（前年対比、例: 0.02=+2%）。長さ<yearsの場合は末尾を引き伸ばし。
    - vacancy_rates: 各年の空室率（0〜1想定）。長さ<yearsの場合は末尾を引き伸ばし。
    - round_to_yen: Trueのとき各年の収入合計を円整数で返す。

    戻り値: 各年の dict リスト。キー: year, monthly_rent, rent_change_rate, vacancy_rate, annual_gross, annual_income
    """
    if years <= 0:
        return []
    if monthly_rent < 0 or units <= 0:
        raise ValueError("monthly_rent must be >=0 and units > 0")

    rc = _coerce_rates(rent_change_rates, years, default=0.0) if rent_change_rates is not None else [0.0] * years
    vr = _coerce_rates(vacancy_rates, years, default=0.0) if vacancy_rates is not None else [0.0] * years

    out: List[Dict[str, Any]] = []
    current_monthly = float(monthly_rent)
    for y in range(years):
        rate_rent = float(rc[y])
        rate_vac = float(vr[y])
        # clamp vacancy to [0,1]
        if rate_vac < 0.0:
            rate_vac = 0.0
        if rate_vac > 1.0:
            rate_vac = 1.0
        if y > 0:
            current_monthly = current_monthly * (1.0 + rate_rent)

        annual_gross = current_monthly * 12.0 * units
        annual_income = annual_gross * (1.0 - rate_vac)
        if round_to_yen:
            row = {
                "year": y + 1,
                "monthly_rent": int(round(current_monthly)),
                "rent_change_rate": rate_rent,
                "vacancy_rate": rate_vac,
                "annual_gross": int(round(annual_gross)),
                "annual_income": int(round(annual_income)),
            }
        else:
            row = {
                "year": y + 1,
                "monthly_rent": current_monthly,
                "rent_change_rate": rate_rent,
                "vacancy_rate": rate_vac,
                "annual_gross": annual_gross,
                "annual_income": annual_income,
            }
        out.append(row)
    return out


def _find_project_config() -> str:
    from pathlib import Path
    here = Path(__file__).resolve().parent
    for _ in range(6):
        cfg = here / "project_config.yml"
        if cfg.exists():
            return str(cfg)
        if here.parent == here:
            break
        here = here.parent
    return ""


def compute_income_from_config(yaml_path: Optional[str] = None, years: int = 40, round_to_yen: bool = True) -> List[Dict[str, Any]]:
    """
    YAML から賃料・変動率・空室率を読み取り、compute_income を実行。

    期待する YAML 例:

    income:
      monthly_rent: 85000      # 1戸あたり月額（円）
      units: 12                # 戸数（省略時1）
      rent_change_rates:       # 年ごとの賃料変動率（少数、0.02=+2%）
        - 0.02
        - 0.01
      vacancy_rates:           # 年ごとの空室率（0〜1）
        - 0.05
        - 0.06
    """
    if yaml is None:
        raise RuntimeError("PyYAML is required to load config YAML (install pyyaml)")

    if yaml_path is None:
        yaml_path = _find_project_config()
        if not yaml_path:
            raise FileNotFoundError("project_config.yml not found; provide yaml_path")
    if not os.path.exists(yaml_path):
        raise FileNotFoundError(yaml_path)

    with open(yaml_path, "r", encoding="utf-8") as fh:
        cfg = yaml.safe_load(fh) or {}
    section = cfg.get("income", {}) or {}
    monthly_rent_val = section.get("monthly_rent", 0.0)
    monthly_rent = to_float(monthly_rent_val, 0.0)
    annual_rent_val = section.get("annual_rent", None)
    if monthly_rent <= 0 and annual_rent_val is not None:
        monthly_rent = to_float(annual_rent_val, 0.0) / 12.0
    units = to_int(section.get("units", 1), 1)
    # rent change: list OR trend specification
    rc = section.get("rent_change_rates", None)
    rc_list: List[float]
    if rc is not None:
        rc_list = _coerce_rates(rc, years, default=0.0)
    else:
        # trend-based keys (both flat and nested forms accepted)
        rent_change = section.get("rent_change", {}) or {}
        initial = rent_change.get("initial", section.get("rent_change_rate_initial", 0.0))
        trend = rent_change.get("trend", section.get("rent_change_rate_trend", 0.0))
        try:
            rc_list = _gen_trend_series(float(initial), float(trend), years)
        except Exception:
            rc_list = [0.0] * years

    # vacancy rate: list OR trend specification
    vr = section.get("vacancy_rates", None)
    vr_list: List[float]
    if vr is not None:
        vr_list = _coerce_rates(vr, years, default=0.0)
    else:
        vacancy = section.get("vacancy", {}) or {}
        v_initial = vacancy.get("initial", section.get("vacancy_rate_initial", 0.0))
        v_trend = vacancy.get("trend", section.get("vacancy_rate_trend", 0.0))
        try:
            vr_list = _gen_trend_series(float(v_initial), float(v_trend), years)
        except Exception:
            vr_list = [0.0] * years
    return compute_income(
        monthly_rent=monthly_rent,
        units=units,
        years=years,
        rent_change_rates=rc_list,
        vacancy_rates=vr_list,
        round_to_yen=round_to_yen,
    )


def sum_income(rows: List[Dict[str, Any]]) -> float:
    """行配列から annual_income の合計を返す（丸め済み整数想定）。"""
    return float(sum(r.get("annual_income", 0) for r in rows))
