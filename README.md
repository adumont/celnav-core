# celnav-core

Shared celestial navigation core library — extracted from [Polaris2](https://github.com/anomalyco/polaris2).

Provides reusable primitives: altitude/azimuth computation, visible body listing, sextant sight simulation (Hs/Ho), sight reduction (Hc/Zn/intercept), least-squares fix solving, fix error computation, and matplotlib chart plotting.

## Quickstart

```bash
uv add celnav-core       # or pip install celnav-core
```

## Use cases

### Take a sextant sight from real position → Hs

```python
from celnav_core.core.sight import compute_ho
from celnav_core.core.almanac import visible_bodies
from celnav_core.models import Position
from datetime import UTC, datetime

pos = Position(lat=34.0, lon=-120.0)
dt = datetime(2026, 6, 21, 14, 0, 0, tzinfo=UTC)

# What bodies are visible?
bodies = visible_bodies(dt, pos)       # → ["Sun", "Venus", ...]

# Take a sight on the Sun (lower limb — default)
reading = compute_ho("Sun", dt, pos, he_ft=10.0)

# Upper limb (Moon):
reading = compute_ho("Moon", dt, pos, he_ft=10.0, limb="Upper")

# Center (planet/star — no limb correction):
reading = compute_ho("Mars", dt, pos, he_ft=10.0, limb="Center")
reading.hs                              # → 52.345°  (raw sextant altitude)
reading.ho                              # → 52.448°  (observed altitude = geometric)
reading.azimuth                         # → 134.2°   (apparent azimuth)
reading.correction_total                # → +0.103°  (dip + refraction + sd)
reading.dip_arcmin                      # → 3.1      (dip in arcminutes)
reading.refraction_arcmin               # → 0.5      (refraction in arcminutes)
reading.semidiameter_arcmin             # → 16.0     (semidiameter in arcminutes)
```

### Reduce the sight at DR position → Hc, Zn, intercept

```python
from celnav_core.core.reduction import compute_hc_zn

dr_pos = Position(lat=35.0, lon=-121.5)
red = compute_hc_zn("Sun", dt, dr_pos, reading.ho, hs=reading.hs)

red.hc                                    # → 52.8°  (computed altitude at DR)
red.azimut_zn                             # → 182.3° (azimuth from DR)
red.intercept_nmi                         # → -0.4   (Ho − Hc in nmi, negative = away)
```

### Solve a fix from 2+ sights

```python
from celnav_core.core.reduction import solve_fix_least_squares, solve_fix_single

# Single LOP → estimated fix at closest point on the LOP
fix = solve_fix_single(red1, dr_pos)

# 2+ sights → least-squares fix (best intersection)
fix = solve_fix_least_squares([red1, red2, red3], dr_pos)

# Or solve from raw (intercept, azimuth) pairs without SightReduction objects:
from celnav_core.core.reduction import solve_fix_from_intercepts
intercepts = [(6.0, 90.0), (-3.0, 180.0), (4.0, 315.0)]
fix = solve_fix_from_intercepts(intercepts, dr_pos)

# Great-circle error from known real position
from celnav_core.core.reduction import compute_fix_error, haversine_distance
fix = compute_fix_error(fix, real_pos)
fix.error_nmi                             # → 2.3 nmi

# Or compute distance between any two positions:
d = haversine_distance(Position(lat=36.5, lon=-6.3), Position(lat=28.5, lon=-16.3))
                                          # → ~697 nmi (Cadiz → Tenerife)
```

### Suggest best body combinations by azimuth geometry

```python
from celnav_core.core.reduction import suggest_best_lops

suggestion = suggest_best_lops(reductions)
# {2: ([0, 2], 1.4), 3: ([0, 2, 3], 2.1)}
# Best 2-body and 3-body combos by lowest condition number
```

### Plot a navigation chart

```python
from celnav_core.cartography import plot_chart

fig = plot_chart(scenario, zoom=1.5)   # DR-centered flat-plane chart
fig.savefig("chart.png")
```

## API reference

### Data classes (`celnav_core.models`)

| Class | Fields | Methods |
|-------|--------|---------|
| `Position` | `lat: float, lon: float` | `.display(fmt="dms")` → str |
| `SextantReading` | `body_name, hs, ho, utc, real_altitude, azimuth, correction_total, dip_arcmin, refraction_arcmin, semidiameter_arcmin` | |
| `SightReduction` | `body_name, hs, ho, hc, intercept_nmi, azimut_zn, lat_dr, lon_dr, utc, selected=True` | |
| `Fix` | `lat, lon, error_nmi=None, iterations=0` | |
| `Scenario` | `real_position, estimated_position, dr_error_nmi, utc, he_ft, sextant_readings=[], sight_reductions=[], fix=None` | |

### Angle utilities (`celnav_core.utils.angles`)

| Function | Input | Output |
|----------|-------|--------|
| `deg_to_ddmmss(v)` | float deg | float `DD.MMSS` |
| `deg_to_ddmmmm(v)` | float deg | float `DD.MMmm` |
| `ddmmss_to_deg(v)` | `DD.MMSS` float | float deg |
| `ddmmmm_to_deg(v)` | `DD.MMmm` float | float deg |
| `round_to_arcsec(v)` | float deg | float deg (rounded) |
| `parse_angle(v)` | auto-detect `DDMMSS`/`DDMMmm` | float deg |
| `format_angle(v, fmt)` | float deg, `"dms"`/`"dmm"` | str `D°MM'SS"` |
| `format_azimuth(v)` | float deg | str `182.3°` |
| `format_position(lat, lon, fmt)` | float lat, lon, fmt | str `34°00'00" N, 120°00'00" W` |
| `body_label(name)` | body name | str `"Sun L"`, `"Venus"`, `"Sirius (18)"` |
| `format_navpac_dmmss(deg)` | float deg | str `"36.3139"` — HP-41C NavPac `DD.MMSS` |
| `parse_dms_string(s)` | str | float deg — parse `"40º26'46\"N"` |

### Celestial computation (`celnav_core.core.ephemeris`)

| Function | Returns | Notes |
|----------|---------|-------|
| `body_alt_az(name, dt, pos, apparent=True)` | `(alt_deg, az_deg)` | Core computation. Geo/refraction via `apparent` flag |
| `ephemeris()` | Skyfield `BSP` | Lazy-loaded DE421 |
| `timescale()` | Skyfield `Timescale` | |
| `earth()` | Earth segment | |

### High-level almanac (`celnav_core.core.almanac`)

| Function | Returns |
|----------|---------|
| `body_alt_az_multiple(names, dt, pos)` | `dict[name → (alt, az)]` |
| `sun_alt_az(dt, pos)` | `(alt, az)` |
| `moon_alt_az(dt, pos)` | `(alt, az)` |
| `visible_bodies(dt, pos, min_alt=10.0)` | `list[str]` — above altitude threshold |

### Sextant sight (`celnav_core.core.sight`)

| Function | Returns | Notes |
|----------|---------|-------|
| `compute_ho(body_name, dt, real_pos, he_ft, limb="Lower")` | `SextantReading` | Full sight: Hs, Ho, azimuth, per-correction breakdown. `limb` ∈ `"Lower"`, `"Upper"`, `"Center"` |
| `dip_correction(he_ft)` | `float` deg | Dip = `-0.97 * sqrt(he_ft)` in arcmin → deg |
| `semidiameter_deg(body_name)` | `float` deg | Sun ~0.267°, Moon ~0.259°, 0 for planets/stars |

### Sight reduction + fix (`celnav_core.core.reduction`)

| Function | Returns | Notes |
|----------|---------|-------|
| `compute_hc_zn(body, dt, dr_pos, ho, hs=0)` | `SightReduction` | Hc (geometric), Zn, intercept `(Ho−Hc)×60` |
| `solve_fix_single(red, dr_pos)` | `Fix` | Single LOP closest approach |
| `solve_fix_least_squares(reductions, dr_pos)` | `Fix` | LSQ A·x = b where A=[cos Zn, sin Zn] |
| `solve_fix_from_intercepts(intercepts, dr)` | `Fix` | Raw `[(intercept_nmi, az_deg), ...]` pairs, no SightReduction needed |
| `haversine_distance(p1, p2)` | float nmi | Great-circle distance between two Position objects |
| `recompute_fix(scenario)` | `None` | Mutates scenario.fix from selected reductions |
| `suggest_best_lops(reductions)` | `dict` | Best 2&3-body combos by condition number |
| `compute_fix_error(fix, real_pos)` | `Fix` | Great-circle distance (via `haversine_distance`) in nmi |

### Cartography (`celnav_core.cartography`)

| Function | Returns | Notes |
|----------|---------|-------|
| `plot_chart(scenario, zoom=1.5)` | `matplotlib.Figure` | Flat-plane LOP chart with compass rose |

## Key decisions

| Aspect | Convention |
|--------|-----------|
| Refraction | `apparent=True` → standard (10°C, 1010 mbar); `apparent=False` → geometric |
| Ho | Geometric altitude (center, no refraction) |
| Hc | Geometric altitude at DR position |
| Sun/Moon Hs | Lower limb: `apparent_alt + dip - sd`. Upper limb: `apparent_alt + dip + sd`. Center: `apparent_alt + dip` |
| Planet/star Hs | Center: `apparent_alt + dip` (sd=0) |
| Correction total | `dip + (geometric−apparent) + sd`. Always satisfies `hs + corr = ho` |
| Intercept | `Ho − Hc` in nmi. Positive = toward body (Zn direction) |
| Fix solver | LSQ: A=[cos(Zn), sin(Zn)], b=intercept vector |
| Fix error | Haversine great-circle distance in nmi |

## Dependencies

- [Skyfield](https://rhodesmill.org/skyfield/) (ephemeris)
- [Pydantic](https://docs.pydantic.dev/) (models)
- NumPy (solver)
- Matplotlib (charts)
