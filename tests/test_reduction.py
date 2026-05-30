import math
import pytest
from celnav_core.models import Position, Scenario, SightReduction, Fix
from celnav_core.core.reduction import (
    _lop_condition_number,
    compute_fix_error,
    haversine_distance,
    recompute_fix,
    solve_fix_from_intercepts,
    solve_fix_least_squares,
    solve_fix_single,
    suggest_best_lops,
)
from datetime import datetime, timezone, UTC


class TestComputeFixError:
    def test_zero_error(self):
        pos = Position(lat=30.0, lon=-40.0)
        fix = Fix(lat=30.0, lon=-40.0)
        fix = compute_fix_error(fix, pos)
        assert fix.error_nmi == pytest.approx(0.0, abs=1e-4)

    def test_one_degree_lat(self):
        pos = Position(lat=30.0, lon=-40.0)
        fix = Fix(lat=31.0, lon=-40.0)
        fix = compute_fix_error(fix, pos)
        assert fix.error_nmi == pytest.approx(60.0, abs=0.1)


class TestSolveFixSingle:
    def test_basic(self):
        dr = Position(lat=30.0, lon=-40.0)
        reduction = SightReduction(
            body_name="Sun",
            hs=0.0,
            ho=45.0,
            hc=45.1,
            intercept_nmi=-6.0,
            azimut_zn=90.0,
            lat_dr=30.0,
            lon_dr=-40.0,
            utc=datetime(2026, 6, 21, 12, 0, 0, tzinfo=UTC),
        )
        fix = solve_fix_single(reduction, dr)
        assert fix.iterations == 1
        assert isinstance(fix.lat, float)
        assert isinstance(fix.lon, float)

    def test_toward_north(self):
        dr = Position(lat=30.0, lon=-40.0)
        reduction = SightReduction(
            body_name="Sun",
            hs=0.0,
            ho=45.0,
            hc=44.0,
            intercept_nmi=60.0,
            azimut_zn=0.0,
            lat_dr=30.0,
            lon_dr=-40.0,
            utc=datetime(2026, 6, 21, 12, 0, 0, tzinfo=UTC),
        )
        fix = solve_fix_single(reduction, dr)
        assert fix.lat == pytest.approx(31.0, abs=0.01)
        assert fix.lon == pytest.approx(-40.0, abs=0.01)


class TestSolveFixLeastSquares:
    def test_two_reductions(self):
        dt = datetime(2026, 6, 21, 12, 0, 0, tzinfo=UTC)
        reductions = [
            SightReduction(
                body_name="Sun",
                hs=0.0,
                ho=45.0,
                hc=45.1,
                intercept_nmi=-6.0,
                azimut_zn=90.0,
                lat_dr=30.0,
                lon_dr=-40.0,
                utc=dt,
            ),
            SightReduction(
                body_name="Moon",
                hs=0.0,
                ho=30.0,
                hc=30.05,
                intercept_nmi=-3.0,
                azimut_zn=180.0,
                lat_dr=30.0,
                lon_dr=-40.0,
                utc=dt,
            ),
        ]
        dr = Position(lat=30.0, lon=-40.0)
        fix = solve_fix_least_squares(reductions, dr)
        assert isinstance(fix.lat, float)
        assert isinstance(fix.lon, float)
        assert fix.iterations >= 1

    def test_too_few_bodies_breaks_early(self):
        dr = Position(lat=30.0, lon=-40.0)
        fix = solve_fix_least_squares([], dr)
        assert isinstance(fix, Fix)


class TestRecomputeFix:
    def test_uses_only_selected(self):
        dt = datetime(2026, 6, 21, 12, 0, 0, tzinfo=UTC)
        reductions = [
            SightReduction(
                body_name="Sun",
                hs=0.0,
                ho=45.0,
                hc=45.1,
                intercept_nmi=-6.0,
                azimut_zn=90.0,
                lat_dr=30.0,
                lon_dr=-40.0,
                utc=dt,
                selected=True,
            ),
            SightReduction(
                body_name="Moon",
                hs=0.0,
                ho=30.0,
                hc=30.05,
                intercept_nmi=-3.0,
                azimut_zn=180.0,
                lat_dr=30.0,
                lon_dr=-40.0,
                utc=dt,
                selected=True,
            ),
            SightReduction(
                body_name="Venus",
                hs=0.0,
                ho=20.0,
                hc=20.05,
                intercept_nmi=-3.0,
                azimut_zn=45.0,
                lat_dr=30.0,
                lon_dr=-40.0,
                utc=dt,
                selected=False,
            ),
        ]
        real = Position(lat=30.0, lon=-40.0)
        est = Position(lat=30.1, lon=-39.9)
        scenario = Scenario(
            real_position=real,
            estimated_position=est,
            dr_error_nmi=5.0,
            utc=dt,
            he_ft=10.0,
            sight_reductions=reductions,
            fix=None,
        )
        recompute_fix(scenario)
        assert scenario.fix is not None
        assert isinstance(scenario.fix.error_nmi, float)

    def test_single_selected_returns_fix(self):
        dt = datetime(2026, 6, 21, 12, 0, 0, tzinfo=UTC)
        reductions = [
            SightReduction(
                body_name="Sun",
                hs=0.0,
                ho=45.0,
                hc=45.1,
                intercept_nmi=-6.0,
                azimut_zn=90.0,
                lat_dr=30.0,
                lon_dr=-40.0,
                utc=dt,
                selected=True,
            ),
        ]
        real = Position(lat=30.0, lon=-40.0)
        est = Position(lat=30.1, lon=-39.9)
        scenario = Scenario(
            real_position=real,
            estimated_position=est,
            dr_error_nmi=5.0,
            utc=dt,
            he_ft=10.0,
            sight_reductions=reductions,
        )
        recompute_fix(scenario)
        assert scenario.fix is not None
        assert scenario.fix.iterations == 1

    def test_none_when_zero_selected(self):
        dt = datetime(2026, 6, 21, 12, 0, 0, tzinfo=UTC)
        reductions = [
            SightReduction(
                body_name="Sun",
                hs=0.0,
                ho=45.0,
                hc=45.1,
                intercept_nmi=-6.0,
                azimut_zn=90.0,
                lat_dr=30.0,
                lon_dr=-40.0,
                utc=dt,
                selected=False,
            ),
            SightReduction(
                body_name="Moon",
                hs=0.0,
                ho=30.0,
                hc=30.05,
                intercept_nmi=-3.0,
                azimut_zn=180.0,
                lat_dr=30.0,
                lon_dr=-40.0,
                utc=dt,
                selected=False,
            ),
        ]
        real = Position(lat=30.0, lon=-40.0)
        est = Position(lat=30.1, lon=-39.9)
        scenario = Scenario(
            real_position=real,
            estimated_position=est,
            dr_error_nmi=5.0,
            utc=dt,
            he_ft=10.0,
            sight_reductions=reductions,
        )
        recompute_fix(scenario)
        assert scenario.fix is None


class TestLopConditionNumber:
    dt = datetime(2026, 6, 21, 12, 0, 0, tzinfo=UTC)

    def test_orthogonal_is_low(self):
        reds = [
            SightReduction(
                body_name="Sun", hs=0, ho=0, hc=0, intercept_nmi=0, azimut_zn=0.0, lat_dr=0, lon_dr=0, utc=self.dt
            ),
            SightReduction(
                body_name="Moon", hs=0, ho=0, hc=0, intercept_nmi=0, azimut_zn=90.0, lat_dr=0, lon_dr=0, utc=self.dt
            ),
        ]
        cond = _lop_condition_number(reds)
        assert cond == pytest.approx(1.0, abs=0.01)

    def test_colinear_is_high(self):
        reds = [
            SightReduction(
                body_name="Sun", hs=0, ho=0, hc=0, intercept_nmi=0, azimut_zn=45.0, lat_dr=0, lon_dr=0, utc=self.dt
            ),
            SightReduction(
                body_name="Moon", hs=0, ho=0, hc=0, intercept_nmi=0, azimut_zn=45.1, lat_dr=0, lon_dr=0, utc=self.dt
            ),
        ]
        cond = _lop_condition_number(reds)
        assert cond > 100


class TestSuggestBestLops:
    dt = datetime(2026, 6, 21, 12, 0, 0, tzinfo=UTC)

    def test_requires_sun_when_present(self):
        reds = [
            SightReduction(
                body_name="Venus", hs=0, ho=0, hc=0, intercept_nmi=0, azimut_zn=0.0, lat_dr=0, lon_dr=0, utc=self.dt
            ),
            SightReduction(
                body_name="Sun", hs=0, ho=0, hc=0, intercept_nmi=0, azimut_zn=90.0, lat_dr=0, lon_dr=0, utc=self.dt
            ),
            SightReduction(
                body_name="Moon", hs=0, ho=0, hc=0, intercept_nmi=0, azimut_zn=180.0, lat_dr=0, lon_dr=0, utc=self.dt
            ),
            SightReduction(
                body_name="Mars", hs=0, ho=0, hc=0, intercept_nmi=0, azimut_zn=270.0, lat_dr=0, lon_dr=0, utc=self.dt
            ),
        ]
        suggestion = suggest_best_lops(reds)
        assert 2 in suggestion
        assert 3 in suggestion
        for k in (2, 3):
            indices, _ = suggestion[k]
            assert 1 in indices  # Sun is at index 1 (0-based)

    def test_fewer_than_two_returns_empty(self):
        reds = [
            SightReduction(
                body_name="Sun", hs=0, ho=0, hc=0, intercept_nmi=0, azimut_zn=90.0, lat_dr=0, lon_dr=0, utc=self.dt
            ),
        ]
        assert suggest_best_lops(reds) == {}

    def test_no_sun_works_without_restriction(self):
        reds = [
            SightReduction(
                body_name="Moon", hs=0, ho=0, hc=0, intercept_nmi=0, azimut_zn=0.0, lat_dr=0, lon_dr=0, utc=self.dt
            ),
            SightReduction(
                body_name="Venus", hs=0, ho=0, hc=0, intercept_nmi=0, azimut_zn=90.0, lat_dr=0, lon_dr=0, utc=self.dt
            ),
            SightReduction(
                body_name="Mars", hs=0, ho=0, hc=0, intercept_nmi=0, azimut_zn=45.0, lat_dr=0, lon_dr=0, utc=self.dt
            ),
        ]
        suggestion = suggest_best_lops(reds)
        assert 2 in suggestion
        assert 3 in suggestion

    def test_picks_orthogonal_pair(self):
        reds = [
            SightReduction(
                body_name="Sun", hs=0, ho=0, hc=0, intercept_nmi=0, azimut_zn=0.0, lat_dr=0, lon_dr=0, utc=self.dt
            ),
            SightReduction(
                body_name="Venus", hs=0, ho=0, hc=0, intercept_nmi=0, azimut_zn=10.0, lat_dr=0, lon_dr=0, utc=self.dt
            ),
            SightReduction(
                body_name="Moon", hs=0, ho=0, hc=0, intercept_nmi=0, azimut_zn=90.0, lat_dr=0, lon_dr=0, utc=self.dt
            ),
        ]
        suggestion = suggest_best_lops(reds)
        indices, _ = suggestion[2]
        # Sun at index 0 + Moon at index 2 (Zn 0+90=90° apart) is best
        assert 0 in indices
        assert 2 in indices


class TestHaversineDistance:
    def test_zero(self):
        pos = Position(lat=30.0, lon=-40.0)
        assert haversine_distance(pos, pos) == pytest.approx(0.0, abs=1e-4)

    def test_equator_degree(self):
        p1 = Position(lat=0.0, lon=0.0)
        p2 = Position(lat=0.0, lon=1.0)
        assert haversine_distance(p1, p2) == pytest.approx(60.0, abs=0.1)

    def test_meridian_degree(self):
        p1 = Position(lat=0.0, lon=0.0)
        p2 = Position(lat=1.0, lon=0.0)
        assert haversine_distance(p1, p2) == pytest.approx(60.0, abs=0.1)

    def test_45_parallel(self):
        p1 = Position(lat=45.0, lon=0.0)
        p2 = Position(lat=45.0, lon=1.0)
        expected = 60.0 * math.cos(math.radians(45.0))
        assert haversine_distance(p1, p2) == pytest.approx(expected, abs=0.1)

    def test_symmetric(self):
        p1 = Position(lat=30.0, lon=-40.0)
        p2 = Position(lat=35.0, lon=-50.0)
        assert haversine_distance(p1, p2) == pytest.approx(haversine_distance(p2, p1), abs=1e-4)

    def test_known_value(self):
        p1 = Position(lat=36.5, lon=-6.3)
        p2 = Position(lat=28.5, lon=-16.3)
        d = haversine_distance(p1, p2)
        assert d == pytest.approx(697.0, abs=5.0)  # ~697 nmi Cadiz to Tenerife


class TestSolveFixFromIntercepts:
    def test_two_perpendicular(self):
        dr = Position(lat=0.0, lon=0.0)
        intercepts = [(10.0, 0.0), (10.0, 90.0)]
        fix = solve_fix_from_intercepts(intercepts, dr)
        assert fix.lat == pytest.approx(10.0 / 60.0, abs=1e-4)
        assert fix.lon == pytest.approx(10.0 / 60.0, abs=1e-4)
        assert fix.iterations == 1

    def test_single_returns_dr(self):
        dr = Position(lat=30.0, lon=-40.0)
        fix = solve_fix_from_intercepts([(10.0, 0.0)], dr)
        assert fix.lat == 30.0
        assert fix.lon == -40.0
        assert fix.iterations == 0

    def test_empty_returns_dr(self):
        dr = Position(lat=30.0, lon=-40.0)
        fix = solve_fix_from_intercepts([], dr)
        assert fix.lat == 30.0
        assert fix.lon == -40.0
        assert fix.iterations == 0

    def test_three_intercepts(self):
        dr = Position(lat=30.0, lon=-40.0)
        intercepts = [(10.0, 0.0), (10.0, 120.0), (10.0, 240.0)]
        fix = solve_fix_from_intercepts(intercepts, dr)
        assert isinstance(fix.lat, float)
        assert isinstance(fix.lon, float)
        assert fix.iterations == 1

    def test_anti_parallel(self):
        dr = Position(lat=0.0, lon=0.0)
        intercepts = [(10.0, 0.0), (10.0, 180.0)]
        fix = solve_fix_from_intercepts(intercepts, dr)
        # North 10 nmi, South 10 nmi — latitude cancels, longitude untouched
        assert fix.lat == pytest.approx(0.0, abs=0.001)
        assert fix.lon == pytest.approx(0.0, abs=0.001)
