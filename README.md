# celnav-core

Shared celestial navigation core library — extracted from [Polaris2](https://github.com/anomalyco/polaris2).

Provides reusable primitives for apps that need celestial navigation: altitude/azimuth computation, visible body listing, sextant sight simulation (Hs/Ho), sight reduction (Hc/Zn/intercept), least-squares fix solving, fix error computation, and matplotlib chart plotting.

## Quickstart

```bash
uv sync
```

## Usage

```python
from celnav_core.core.sight import compute_ho
from celnav_core.core.almanac import visible_bodies
from celnav_core.core.reduction import compute_hc_zn, solve_fix_least_squares
from celnav_core.models import Position

pos = Position(lat=34.0, lon=-120.0)
dt = datetime(2026, 6, 21, 14, 0, 0, tzinfo=UTC)

# List visible bodies
bodies = visible_bodies(dt, pos)

# Take a sight
reading = compute_ho("Sun", dt, pos, he_ft=10.0)
print(f"Hs = {reading.hs:.4f}°")

# Reduce it
red = compute_hc_zn("Sun", dt, dr_pos, reading.ho, hs=reading.hs)
```

## Key decisions

| Aspect | Convention |
|--------|-----------|
| Refraction | `apparent=True` for standard refraction (10°C, 1010 mbar); `apparent=False` for geometric |
| Ho | Geometric altitude (center, no refraction) |
| Hc | Geometric altitude at DR position |
| Sun/Moon Hs | Lower limb: `apparent_alt - dip - sd` |
| Planet/star Hs | Center: `apparent_alt - dip` (sd=0) |
| Intercept | `Ho - Hc` in nmi. Positive = Toward body (Zn direction) |
| Fix solver | LSQ: A=[cos(Zn), sin(Zn)], b=intercept vector |
| Fix error | Haversine great-circle distance in nmi |

## Dependencies

- [Skyfield](https://rhodesmill.org/skyfield/) (ephemeris)
- [Pydantic](https://docs.pydantic.dev/) (models)
- NumPy (solver)
- Matplotlib (charts)
