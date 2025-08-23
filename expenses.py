from typing import List, Dict, Any, Optional
from pathlib import Path
import csv
import os

from utils import to_float, to_int  # type: ignore
from tax import compute_annual_taxes  # type: ignore
from loan import loan_schedule_annually  # type: ignore
from income import compute_income_from_config  # type: ignore

try:
    import yaml  # type: ignore
except Exception:
    yaml = None


def _find_project_config() -> str:
    here = Path(__file__).resolve().parent
    for _ in range(6):
        cfg = here / "project_config.yml"
        if cfg.exists():
            return str(cfg)
        if here.parent == here:
            break
        here = here.parent
    return ""


def _load_yearly_amounts_csv(path: Optional[str], years: int) -> List[float]:
    """Load year-indexed amounts from CSV. Supports:
    - Single column: sequential amounts per year starting from year 1
    - Pair columns: year, amount (1-based year)
    Ignores blank lines and lines starting with '#'.
    If file missing/None -> zeros.
    """
    if not path:
        return [0.0] * years

    candidates: List[Path] = []
    p = Path(path)
    candidates.append(p)
    base = Path(__file__).parent
    candidates.append(base / "data" / p.name)
    candidates.append(base / "examples" / p.name)

    chosen: Optional[Path] = None
    for c in candidates:
        if c.exists() and c.suffix.lower() == ".csv":
            chosen = c
            break
    if not chosen:
        return [0.0] * years

    text = chosen.read_text(encoding="utf-8")
    rows = []
    for line in text.splitlines():
        line = line.strip()
        if not line or line.startswith("#"):
            continue
        rows.append(next(csv.reader([line])))
    if not rows:
        return [0.0] * years

    is_pair = any(len(r) >= 2 for r in rows)
    out = [0.0] * years
    if is_pair:
        for r in rows:
            try:
                y = int(float(r[0]))
                amt = to_float(r[1], 0.0)
            except Exception:
                continue
            if 1 <= y <= years:
                out[y - 1] = amt
        return out
    else:
        vals: List[float] = []
        for r in rows:
            try:
                vals.append(to_float(r[0], 0.0))
            except Exception:
                vals.append(0.0)
        if len(vals) >= years:
            return vals[:years]
        vals.extend([0.0] * (years - len(vals)))
        return vals


def _load_repairs_three_col_csv(path: Optional[str], years: int) -> Optional[tuple[List[float], List[float]]]:
    """Load a combined repairs CSV with columns: year, capex_large, equipment_repairs.

    Returns a tuple (capex_large_list, equipment_repairs_list) if loaded, else None.
    Supports comment lines starting with '#'.
    """
    if not path:
        return None
    candidates: List[Path] = []
    p = Path(path)
    candidates.append(p)
    base = Path(__file__).parent
    candidates.append(base / "data" / p.name)
    candidates.append(base / "examples" / p.name)
    chosen: Optional[Path] = None
    for c in candidates:
        if c.exists() and c.suffix.lower() == ".csv":
            chosen = c
            break
    # DEBUG: show which candidate paths we considered (temporary)
    # print("_load_repairs_three_col_csv: candidates=", [str(x) for x in candidates])
    # print("_load_repairs_three_col_csv: chosen=", str(chosen) if chosen else None)
    if not chosen:
        return None

    text = chosen.read_text(encoding="utf-8")
    rows: List[List[str]] = []
    for line in text.splitlines():
        s = line.strip()
        if not s or s.startswith('#'):
            continue
        rows.append(next(csv.reader([s])))
    if not rows:
        return None

    cap = [0.0] * years
    eq = [0.0] * years
    # detect header: first row col0 not a number
    start_idx = 0
    try:
        float(rows[0][0])
    except Exception:
        start_idx = 1
    for r in rows[start_idx:]:
        if len(r) < 3:
            continue
        try:
            y = int(float(r[0]))
            cap_v = to_float(r[1], 0.0)
            eq_v = to_float(r[2], 0.0)
        except Exception:
            continue
        if 1 <= y <= years:
            cap[y - 1] = cap_v
            eq[y - 1] = eq_v
    return (cap, eq)


def compute_expenses(
    *,
    years: int,
    # Taxes inputs
    land_assessed_value: float,
    building_assessed_value: float,
    land_area_m2: float = 0.0,
    units: int = 1,
    fixed_asset_rate: Optional[float] = None,
    city_plan_rate: Optional[float] = None,
    building_correction_rates_csv: Optional[str] = None,
    land_residential_special: bool = True,
    # Loan inputs
    loan_principal: float = 0.0,
    loan_annual_rate: float = 0.0,
    loan_years: int = 0,
    loan_start_month: int = 1,
    loan_method: str = "equal_total",
    loan_group_by: str = "calendar",
    loan_rate_schedule: Optional[List[Dict[str, Any]]] = None,
    # Operations (fixed annual costs)
    op_management_fee: float = 0.0,
    op_management_fee_rate: Optional[float] = None,
    op_repairs: float = 0.0,
    op_insurance: float = 0.0,
    op_utilities: float = 0.0,
    # Operations (CSV year-by-year)
    op_capex_large_csv: Optional[str] = None,
    op_equipment_repairs_csv: Optional[str] = None,
    op_repairs_plan_csv: Optional[str] = None,
    round_to_yen: bool = True,
) -> List[Dict[str, Any]]:
    """Compute yearly expenses breakdown and totals.

    Returns list of dicts per year with keys:
    - year
    - fixed_tax_land, city_tax_land, fixed_tax_building, city_tax_building, taxes_total
    - loan_principal, loan_interest, loan_total
    - management_fee, repairs, insurance, utilities, capex_large, equipment_repairs, operations_total
    - total_expenses
    """
    if years <= 0:
        return []

    # Taxes
    tax_rows = compute_annual_taxes(
        land_assessed_value=to_float(land_assessed_value, 0.0),
        building_assessed_value=to_float(building_assessed_value, 0.0),
        land_area_m2=to_float(land_area_m2, 0.0),
        units=to_int(units, 1),
        years=years,
        fixed_asset_rate=fixed_asset_rate if fixed_asset_rate is not None else 0.014,
        city_plan_rate=city_plan_rate if city_plan_rate is not None else 0.003,
        loan_config_rate_file=building_correction_rates_csv,
        land_residential_special=land_residential_special,
    )

    # Loan
    loan_rows: List[Dict[str, Any]] = []
    if loan_principal and loan_years:
        # inject optional rate schedule by setting module variable if provided
        if loan_rate_schedule:
            import loan as _loan_mod  # type: ignore
            _loan_mod.rate_schedule = loan_rate_schedule
        sched = loan_schedule_annually(
            principal=to_float(loan_principal, 0.0),
            annual_rate=to_float(loan_annual_rate, 0.0),
            years=int(loan_years),
            start_month=int(loan_start_month),
            method=str(loan_method),
            group_by=str(loan_group_by),
        )
        loan_rows = sched.get("annual", [])

    # Operations
    # Prefer combined CSV if provided; else fall back to separate CSVs
    capex_large: List[float]
    equip_repairs: List[float]
    combined = _load_repairs_three_col_csv(op_repairs_plan_csv, years)
    if combined is not None:
        capex_large, equip_repairs = combined
    else:
        capex_large = _load_yearly_amounts_csv(op_capex_large_csv, years)
        equip_repairs = _load_yearly_amounts_csv(op_equipment_repairs_csv, years)

    # Pre-compute income rows if management fee is rate-based
    income_rows: Optional[List[Dict[str, Any]]] = None
    if op_management_fee_rate is not None and op_management_fee_rate != 0:
        try:
            income_rows = compute_income_from_config(years=years, round_to_yen=True)
        except Exception:
            income_rows = None

    rows: List[Dict[str, Any]] = []
    for y in range(years):
        t = tax_rows[y]
        # Loan values for this year (if available)
        lp = li = lt = 0.0
        if y < len(loan_rows):
            yr = loan_rows[y]
            lp = float(yr.get("principal_paid", 0.0))
            li = float(yr.get("interest_paid", 0.0))
            lt = float(yr.get("total_paid", lp + li))

        # Fixed ops
        # Management fee: either fixed yen or percentage of annual rental income
        if op_management_fee_rate is not None and income_rows and y < len(income_rows):
            base_income = float(income_rows[y].get("annual_income", 0.0))
            mgmt = base_income * float(op_management_fee_rate)
        else:
            mgmt = to_float(op_management_fee, 0.0)
        reps = to_float(op_repairs, 0.0)
        ins = to_float(op_insurance, 0.0)
        util = to_float(op_utilities, 0.0)
        cap = float(capex_large[y])
        erep = float(equip_repairs[y])
        ops_total = mgmt + reps + ins + util + cap + erep

        taxes_total = float(t["fixed_tax_land"]) + float(t["city_tax_land"]) + float(t["fixed_tax_building"]) + float(t["city_tax_building"])

        total = taxes_total + lt + ops_total

        row: Dict[str, Any] = {
            "year": y + 1,
            # Taxes
            "fixed_tax_land": t["fixed_tax_land"],
            "city_tax_land": t["city_tax_land"],
            "fixed_tax_building": t["fixed_tax_building"],
            "city_tax_building": t["city_tax_building"],
            "taxes_total": taxes_total,
            # Loan
            "loan_principal": lp,
            "loan_interest": li,
            "loan_total": lt,
            # Operations
            "management_fee": mgmt,
            "repairs": reps,
            "insurance": ins,
            "utilities": util,
            "capex_large": cap,
            "equipment_repairs": erep,
            "operations_total": ops_total,
            # Total
            "total_expenses": total,
        }

        if round_to_yen:
            for k in (
                "fixed_tax_land",
                "city_tax_land",
                "fixed_tax_building",
                "city_tax_building",
                "taxes_total",
                "loan_principal",
                "loan_interest",
                "loan_total",
                "management_fee",
                "repairs",
                "insurance",
                "utilities",
                "capex_large",
                "equipment_repairs",
                "operations_total",
                "total_expenses",
            ):
                row[k] = int(round(float(row[k])))

        rows.append(row)

    return rows


def compute_expenses_from_config(yaml_path: Optional[str] = None, years: int = 40, round_to_yen: bool = True) -> List[Dict[str, Any]]:
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

    # Taxes config (allow both top-level and under 'taxes')
    taxes_cfg = cfg.get("taxes", {}) or {}
    land_val = to_float(taxes_cfg.get("land_assessed_value", cfg.get("land_assessed_value", 0.0)), 0.0)
    bld_val = to_float(taxes_cfg.get("building_assessed_value", cfg.get("building_assessed_value", 0.0)), 0.0)
    land_area_m2 = to_float(taxes_cfg.get("land_area_m2", cfg.get("land_area_m2", 0.0)), 0.0)
    # units: prefer income.units if not explicitly set in taxes
    units_val = taxes_cfg.get("units", cfg.get("units", None))
    if units_val is None:
        units_val = ((cfg.get("income", {}) or {}).get("units", 1))
    units_i = to_int(units_val, 1)
    fixed_asset_rate = taxes_cfg.get("fixed_asset_rate", cfg.get("fixed_asset_rate", None))
    city_plan_rate = taxes_cfg.get("city_plan_rate", cfg.get("city_plan_rate", None))
    bld_corr_csv = taxes_cfg.get("building_correction_rates_csv", cfg.get("building_correction_rates_csv", None))
    land_res_special = taxes_cfg.get("land_residential_special", True)

    # If building_assessed_value not explicitly provided, try to derive it
    # from the depreciation/building section in the YAML (building.cost and equipment.cost).
    # If equipment.cost is missing or zero, split building.cost as 85% building / 15% equipment.
    try:
        if not bld_val:
            bld_section = cfg.get("building", {}) or {}
            eq_section = cfg.get("equipment", {}) or {}
            bld_cost = to_float(bld_section.get("cost", 0.0), 0.0)
            eq_cost = to_float(eq_section.get("cost", 0.0), 0.0)
            if bld_cost and (not eq_cost):
                # split into building/equipment per project convention
                bld_val = float(bld_cost) * 0.85
            elif bld_cost:
                # use building.cost as building assessed value
                bld_val = float(bld_cost)
    except Exception:
        # on any error, keep existing bld_val (defaults applied earlier)
        pass

    # If land_assessed_value is zero or missing, try to estimate it from building cost
    # (fallback heuristic: land = 20% of building cost). This avoids zero land tax when
    # the user did not provide land assessment explicitly.
    try:
        if not land_val:
            bld_section = cfg.get("building", {}) or {}
            bld_cost = to_float(bld_section.get("cost", 0.0), 0.0)
            if bld_cost:
                land_val = float(bld_cost) * 0.20
    except Exception:
        pass

    # Loan config (top-level keys per existing examples)
    principal = to_float(cfg.get("principal", 0.0), 0.0)
    annual_rate = to_float(cfg.get("annual_rate", 0.0), 0.0)
    loan_years = to_int(cfg.get("years", 0), 0)
    start_month = to_int(cfg.get("start_month", 1), 1)
    method = str(cfg.get("method", "equal_total"))
    group_by = str(cfg.get("group_by", "calendar"))
    rate_schedule = cfg.get("rate_schedule")

    # Operations config
    ops_cfg = (cfg.get("expenses", {}) or {}).get("operations", {}) or {}
    mgmt = to_float(ops_cfg.get("management_fee", 0.0), 0.0)
    mgmt_rate_val = ops_cfg.get("management_fee_rate", None)
    if mgmt_rate_val is None:
        # also accept percent-style key for convenience
        mgmt_rate_val = ops_cfg.get("management_fee_percent", None)
    mgmt_rate: Optional[float] = None
    if mgmt_rate_val is not None:
        try:
            mr = float(mgmt_rate_val)
            if abs(mr) > 1:
                mr = mr / 100.0
            mgmt_rate = mr
        except Exception:
            mgmt_rate = None
    reps = to_float(ops_cfg.get("repairs", 0.0), 0.0)
    ins = to_float(ops_cfg.get("insurance", 0.0), 0.0)
    util = to_float(ops_cfg.get("utilities", 0.0), 0.0)
    cap_csv = ops_cfg.get("capex_large_csv")
    eqr_csv = ops_cfg.get("equipment_repairs_csv")
    combined_repairs_csv = ops_cfg.get("repairs_plan_csv")

    # Backward-compatible fallback: allow CSV keys placed directly under `expenses` (not nested under operations)
    if not combined_repairs_csv:
        combined_repairs_csv = (cfg.get("expenses", {}) or {}).get("repairs_plan_csv")
    if not cap_csv:
        cap_csv = (cfg.get("expenses", {}) or {}).get("capex_large_csv")
    if not eqr_csv:
        eqr_csv = (cfg.get("expenses", {}) or {}).get("equipment_repairs_csv")

    return compute_expenses(
        years=years,
        land_assessed_value=land_val,
        building_assessed_value=bld_val,
        land_area_m2=land_area_m2,
        units=units_i,
        fixed_asset_rate=fixed_asset_rate,
        city_plan_rate=city_plan_rate,
        building_correction_rates_csv=bld_corr_csv,
        land_residential_special=bool(land_res_special),
        loan_principal=principal,
        loan_annual_rate=annual_rate,
        loan_years=loan_years,
        loan_start_month=start_month,
        loan_method=method,
        loan_group_by=group_by,
        loan_rate_schedule=rate_schedule,
    op_management_fee=mgmt,
    op_management_fee_rate=mgmt_rate,
        op_repairs=reps,
        op_insurance=ins,
        op_utilities=util,
    op_capex_large_csv=cap_csv,
    op_equipment_repairs_csv=eqr_csv,
    op_repairs_plan_csv=combined_repairs_csv,
        round_to_yen=round_to_yen,
    )


def sum_expenses(rows: List[Dict[str, Any]]) -> float:
    return float(sum(r.get("total_expenses", 0) for r in rows))
