import re

from celnav_core.config import NAVPAC_STAR_INDEX, PLANET_BODIES


def deg_to_ddmmss(value: float) -> float:
    sign = -1 if value < 0 else 1
    v = abs(value)
    d = int(v)
    m = int((v - d) * 60)
    s = (v - d - m / 60) * 3600
    return sign * (d * 10000 + m * 100 + s)


def deg_to_ddmmmm(value: float) -> float:
    sign = -1 if value < 0 else 1
    v = abs(value)
    d = int(v)
    mm = (v - d) * 60
    return sign * (d * 10000 + mm * 100)


def ddmmss_to_deg(value: float) -> float:
    sign = -1 if value < 0 else 1
    v = abs(value)
    d = int(v // 10000)
    m = int((v - d * 10000) // 100)
    s = v - d * 10000 - m * 100
    return sign * (d + m / 60 + s / 3600)


def ddmmmm_to_deg(value: float) -> float:
    sign = -1 if value < 0 else 1
    v = abs(value)
    d = int(v // 10000)
    mm = (v - d * 10000) / 100
    return sign * (d + mm / 60)


def round_to_arcsec(deg: float) -> float:
    v = abs(deg)
    d = int(v)
    m = int((v - d) * 60)
    s = round((v - d - m / 60) * 3600)
    return (1 if deg >= 0 else -1) * (d + m / 60 + s / 3600)


_DDMMSS_THRESHOLD = 100.0


def parse_angle(value: float) -> float:
    v = abs(value)
    d = int(v // 10000)
    rest = v - d * 10000
    if rest > _DDMMSS_THRESHOLD:
        return ddmmss_to_deg(value)
    else:
        return ddmmmm_to_deg(value)


def _abs_deg_min_sec(v: float) -> tuple[int, int, float]:
    d = int(v)
    m = int((v - d) * 60)
    s = (v - d - m / 60) * 3600
    return d, m, s


def _abs_deg_min(v: float) -> tuple[int, float]:
    d = int(v)
    m = (v - d) * 60
    return d, m


def format_ddmmss(deg: float) -> str:
    d, m, s = _abs_deg_min_sec(abs(deg))
    return f"{d:d}°{m:02d}'{round(s):02d}\""


def format_ddmmmm(deg: float) -> str:
    d, m = _abs_deg_min(abs(deg))
    return f"{d:d}°{m:05.2f}'"


def format_angle(deg: float, fmt: str = "dms") -> str:
    if fmt == "dmm":
        return format_ddmmmm(deg)
    return format_ddmmss(deg)


def body_label(name: str) -> str:
    if name == "Sun":
        return "Sun L"
    if name == "Moon":
        return "Moon L"
    if name in PLANET_BODIES:
        return name
    idx = NAVPAC_STAR_INDEX.get(name)
    if idx is not None:
        return f"{name} ({idx})"
    return name


def format_azimuth(deg: float) -> str:
    return f"{deg:.1f}°"


def format_position(lat: float, lon: float, fmt: str = "dms") -> str:
    ns = "N" if lat >= 0 else "S"
    ew = "E" if lon >= 0 else "W"
    lat_s = format_angle(lat, fmt)
    lon_s = format_angle(lon, fmt)
    return f"{lat_s} {ns}, {lon_s} {ew}"


def format_navpac_dmmss(deg: float) -> str:
    sign = "-" if deg < 0 else ""
    packed = deg_to_ddmmss(abs(deg))
    d = int(packed // 10000)
    mmss = packed - d * 10000
    return f"{sign}{d}.{mmss:04.0f}"


def parse_dms_string(s: str) -> float:
    if not s or not s.strip():
        raise ValueError("Empty string")

    s = s.strip().upper()

    sign = -1 if "S" in s or "W" in s or s[0] == "-" else 1

    s_clean = re.sub(r"[NSEW°º'\"˝-]", " ", s)
    parts = [p for p in re.split(r"[\s:;,_]+", s_clean) if p]

    if not parts:
        raise ValueError(f"Could not parse: {s}")

    deg = float(parts[0])
    minutes = float(parts[1]) if len(parts) > 1 else 0.0
    seconds = float(parts[2]) if len(parts) > 2 else 0.0

    return sign * (deg + minutes / 60.0 + seconds / 3600.0)
