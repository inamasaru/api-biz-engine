import os


def env_int(name: str, default: int) -> int:
    v = os.getenv(name, "").strip()
    try:
        return int(v)
    except Exception:
        return default


def clamp(x: float, lo: float, hi: float) -> float:
    return max(lo, min(hi, x))
