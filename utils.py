from typing import Any


def to_float(value: Any, default: float = 0.0) -> float:
    """Parse value into float. Accepts strings with thousands separators (",")."""
    if value is None:
        return float(default)
    if isinstance(value, (int, float)):
        return float(value)
    try:
        s = str(value).strip().replace(",", "")
        if s == "":
            return float(default)
        return float(s)
    except Exception:
        return float(default)


def to_int(value: Any, default: int = 0) -> int:
    """Parse value into int. Accepts strings with thousands separators (",")."""
    if value is None:
        return int(default)
    if isinstance(value, int):
        return int(value)
    try:
        s = str(value).strip().replace(",", "")
        if s == "":
            return int(default)
        return int(s)
    except Exception:
        return int(default)
