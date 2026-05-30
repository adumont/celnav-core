# Context

- uv based python lib, never bare `python`, always via `uv run`
- modular, not monolithic
- Pydantic models for all data
- Test before handover
- Language: only english!

## Testing and Code Quality

- pytest in tests/
- ruff for lint+format (run: `uv run ruff check --fix .` and `uv run ruff format`)
- Coverage: min 90% overall, 80% per file.

## Commit

- Clean commit, single line (small) or multiline (massive)
- Never `git add .`, only touched files
- Never `--no-ff` on merges — fast-forward only

# Architecture

src/celnav_core/
├── config.py      Constants: NAVPAC star index, body radii, bounds, defaults
├── models.py      Pydantic: Position, SextantReading, SightReduction, Fix, Scenario
├── utils/
│   └── angles.py  DD.MMSS <-> DD.MMmm <-> float deg conversions
├── core/
│   ├── ephemeris.py  Skyfield lazy loader, body_alt_az()
│   ├── almanac.py    visible_bodies(), body_alt_az_multiple()
│   ├── sight.py      compute_ho() — sextant readings
│   └── reduction.py  Hc/Zn, intercept, LSQ fix solver
└── cartography.py    matplotlib chart plotting

# Key decisions

- Skyfield 1.54 API: body.observe() requires observer = EARTH + wgs84.latlon()
- `body_alt_az(apparent=True)` passes `temperature_C=10, pressure_mbar=1010` — altitude WITH standard refraction
- `body_alt_az(apparent=False)` passes `temperature_C=10, pressure_mbar=0` — geometric altitude (no refraction)
- Ho = Skyfield geometric alt (center, no refraction) = same for ALL bodies
- Hc = Skyfield geometric alt at DR position (same `apparent=False` convention as Ho)
- For Sun/Moon: `hs = apparent_alt - dip - sd` = lower limb sextant reading
- For planets/stars: `hs = apparent_alt - dip` = center sextant reading (sd=0)
- `correction_total = dip + (geometric - apparent) + sd` = traditional Hs→Ho correction. Always satisfies `hs + corr = ho`
- intercept = Ho - Hc (nmi). Positive = Toward body (in Zn direction)
- LSQ solver: A = [cos(Zn), sin(Zn)], b = intercept
- Best bodies: 30-60 deg altitude range, fall back to lower/upper, min 2 bodies
- Fix error via haversine formula, nautical miles
