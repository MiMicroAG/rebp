from typing import List, Dict, Optional, Tuple
from pathlib import Path
import csv
import warnings
from utils import to_float  # type: ignore

try:
    import yaml  # type: ignore
except Exception:
    yaml = None


def _load_rates_from_file(path: Optional[str], years: int) -> List[float]:
    """Load yearly multipliers from a CSV file (one value per line).

    If path is None or file missing or not a .csv, returns a list of 1.0s.
    """
    candidates: List[Path] = []
    if not path:
        # Backward compatible default: no file -> all 1.0s
        return [1.0] * years
    else:
        p = Path(path)
        candidates.append(p)
        # If a relative/implicit path was given and not found, try common locations
        here = Path(__file__).parent
        candidates.append(here / "data" / p.name)
        candidates.append(here / "examples" / p.name)

    chosen: Optional[Path] = None
    for p in candidates:
        if p.exists() and p.suffix.lower() == ".csv":
            chosen = p
            break
    if not chosen:
        return [1.0] * years

    text = chosen.read_text(encoding="utf-8")
    # normalize: ignore blank lines and lines starting with '#'
    rows: List[List[str]] = []
    for line in text.splitlines():
        s = line.strip()
        if not s or s.startswith("#"):
            continue
        rows.append(next(csv.reader([s])))
    if not rows:
        return [1.0] * years

    # two supported CSV styles:
    # - pair: year, multiplier per line (year numbers are 1-based)
    # - single column: each line is the multiplier for consecutive years (year1, year2, ...)
    is_pair = any(len(row) >= 2 for row in rows)
    if is_pair:
        out = [1.0] * years
        for row in rows:
            try:
                year_idx = int(float(row[0]))
                rate = float(row[1])
            except Exception:
                continue
            if 1 <= year_idx <= years:
                out[year_idx - 1] = rate
        
        return out
    else:
        vals: List[float] = []
        for row in rows:
            try:
                vals.append(float(row[0]))
            except Exception:
                continue
        if len(vals) >= years:
            return vals[:years]
        vals.extend([1.0] * (years - len(vals)))
        return vals


def _load_tax_rates_from_yaml(path: Optional[str]) -> Optional[Tuple[float, float]]:
    """Load fixed_asset_rate and city_plan_rate from a YAML file.

    Returns tuple (fixed_asset_rate, city_plan_rate) if loaded, else None.
    """
    if not path:
        return None
    p = Path(path)
    if not p.exists():
        return None
    if yaml is None:
        warnings.warn("PyYAML not installed; cannot read YAML tax config; using defaults")
        return None
    try:
        data = yaml.safe_load(p.read_text(encoding="utf-8"))
    except Exception:
        return None
    if not isinstance(data, dict):
        return None
    fa = data.get("fixed_asset_rate")
    cp = data.get("city_plan_rate")
    try:
        if fa is not None:
            fa = float(fa)
        if cp is not None:
            cp = float(cp)
    except Exception:
        return None
    if fa is None or cp is None:
        return None
    return (fa, cp)


def compute_annual_taxes(
    land_assessed_value: float,
    building_assessed_value: float,
    land_area_m2: float,
    units: int,
    years: int = 40,
    fixed_asset_rate: float = 0.014,
    city_plan_rate: float = 0.003,
    loan_config_rate_file: Optional[str] = None,
    land_residential_special: bool = True,
) -> List[Dict[str, float]]:
    """Compute annual taxes for land and building for given years.

    Returns list of dicts per year with keys:
    - fixed_tax_land
    - city_tax_land
    - fixed_tax_building
    - city_tax_building
    - total

    land_residential_special: if None, determine by land_area <= units*200 (per rule)
    loan_config_rate_file: path to YAML/CSV/JSON file listing yearly building correction multipliers
    """
    if years <= 0:
        raise ValueError("years must be > 0")

    # try to load tax rates from unified project YAML config if present
    repo_yaml = Path(__file__).parent.parent / "project_config.yml"
    loaded = _load_tax_rates_from_yaml(str(repo_yaml))
    if loaded is not None:
        fixed_asset_rate, city_plan_rate = loaded

    # residential special: default is True (apply the special).
    # Caller can pass False to disable the special.

    # land taxable base multipliers per provided rule
    if land_residential_special:
        land_fixed_multiplier = 1.0 / 6.0
        land_city_multiplier = 1.0 / 3.0
    else:
        land_fixed_multiplier = 1.0
        land_city_multiplier = 1.0

    # load building correction rates per year (multiplicative against initial assessed value)
    correction_rates = _load_rates_from_file(loan_config_rate_file, years)

    results: List[Dict[str, float]] = []

    # Convert potential strings-with-commas to floats defensively
    land_val = to_float(land_assessed_value)
    bld_val = to_float(building_assessed_value)
    # land taxable bases (assumed constant over years per rule in attachments)
    land_base_fixed = land_val * land_fixed_multiplier
    land_base_city = land_val * land_city_multiplier

    for y in range(years):
        # building assessed value for this year after correction
        building_value = bld_val * correction_rates[y]

        fixed_tax_land = land_base_fixed * fixed_asset_rate
        city_tax_land = land_base_city * city_plan_rate

        fixed_tax_building = building_value * fixed_asset_rate
        city_tax_building = building_value * city_plan_rate

        total = fixed_tax_land + city_tax_land + fixed_tax_building + city_tax_building

        results.append(
            {
                "year": y + 1,
                "fixed_tax_land": fixed_tax_land,
                "city_tax_land": city_tax_land,
                "fixed_tax_building": fixed_tax_building,
                "city_tax_building": city_tax_building,
                "total": total,
            }
        )

    return results
