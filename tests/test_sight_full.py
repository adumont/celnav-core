import pytest
from celnav_core.core.sight import compute_ho, semidiameter_deg
from celnav_core.models import Position
from datetime import datetime, UTC


class TestComputeHo:
    def test_sun_ho(self):
        pos = Position(lat=30.0, lon=-40.0)
        dt = datetime(2026, 6, 21, 14, 0, 0, tzinfo=UTC)
        reading = compute_ho("Sun", dt, pos, 10.0)
        assert reading.body_name == "Sun"
        assert isinstance(reading.ho, float)
        assert reading.ho == reading.real_altitude

    def test_sun_new_fields(self):
        pos = Position(lat=30.0, lon=-40.0)
        dt = datetime(2026, 6, 21, 14, 0, 0, tzinfo=UTC)
        reading = compute_ho("Sun", dt, pos, 10.0)
        assert isinstance(reading.azimuth, float)
        assert reading.dip_arcmin > 0
        assert reading.refraction_arcmin > 0
        assert reading.semidiameter_arcmin > 0

    def test_sun_azimuth_range(self):
        pos = Position(lat=30.0, lon=-40.0)
        dt = datetime(2026, 6, 21, 14, 0, 0, tzinfo=UTC)
        reading = compute_ho("Sun", dt, pos, 10.0)
        assert 0 <= reading.azimuth <= 360

    def test_moon_lower_limb(self):
        sd = semidiameter_deg("Moon")
        assert sd > 0, "Moon must have semi-diameter > 0 for lower limb"

    def test_moon_ho(self):
        pos = Position(lat=30.0, lon=-40.0)
        dt = datetime(2026, 6, 21, 14, 0, 0, tzinfo=UTC)
        reading = compute_ho("Moon", dt, pos, 10.0)
        assert reading.body_name == "Moon"
        assert isinstance(reading.ho, float)

    def test_planet_semidiameter_zero(self):
        pos = Position(lat=30.0, lon=-40.0)
        dt = datetime(2026, 6, 21, 14, 0, 0, tzinfo=UTC)
        reading = compute_ho("Mars", dt, pos, 10.0)
        assert reading.semidiameter_arcmin == pytest.approx(0.0, abs=1e-4)

    def test_limb_parameter_default(self):
        pos = Position(lat=30.0, lon=-40.0)
        dt = datetime(2026, 6, 21, 14, 0, 0, tzinfo=UTC)
        reading_default = compute_ho("Sun", dt, pos, 10.0)
        reading_lower = compute_ho("Sun", dt, pos, 10.0, limb="Lower")
        assert reading_default.hs == pytest.approx(reading_lower.hs, abs=1e-4)

    def test_upper_limb_differs(self):
        pos = Position(lat=30.0, lon=-40.0)
        dt = datetime(2026, 6, 21, 14, 0, 0, tzinfo=UTC)
        lower = compute_ho("Sun", dt, pos, 10.0, limb="Lower")
        upper = compute_ho("Sun", dt, pos, 10.0, limb="Upper")
        sd = semidiameter_deg("Sun")
        # Upper limb hs = apparent_alt - dip + sd, Lower = apparent_alt - dip - sd
        # Difference in hs should be 2 * sd
        assert upper.hs - lower.hs == pytest.approx(2 * sd, abs=1e-4)

    def test_center_limb(self):
        pos = Position(lat=30.0, lon=-40.0)
        dt = datetime(2026, 6, 21, 14, 0, 0, tzinfo=UTC)
        center = compute_ho("Sun", dt, pos, 10.0, limb="Center")
        lower = compute_ho("Sun", dt, pos, 10.0, limb="Lower")
        sd = semidiameter_deg("Sun")
        assert center.hs - lower.hs == pytest.approx(sd, abs=1e-4)

    def test_hs_plus_corr_equals_ho(self):
        pos = Position(lat=30.0, lon=-40.0)
        dt = datetime(2026, 6, 21, 14, 0, 0, tzinfo=UTC)
        reading = compute_ho("Sun", dt, pos, 10.0)
        assert reading.hs + reading.correction_total == pytest.approx(reading.ho, abs=1e-10)

    def test_sun_known_values(self):
        pos = Position(lat=30.0, lon=-40.0)
        dt = datetime(2026, 6, 21, 14, 0, 0, tzinfo=UTC)
        r = compute_ho("Sun", dt, pos, 10.0)
        assert r.hs == pytest.approx(78.381, abs=0.001)
        assert r.ho == pytest.approx(78.593, abs=0.001)
        assert r.azimuth == pytest.approx(122.636, abs=0.01)
        assert r.dip_arcmin == pytest.approx(3.067, abs=0.01)
        assert r.refraction_arcmin == pytest.approx(0.200, abs=0.01)
        assert r.semidiameter_arcmin == pytest.approx(15.987, abs=0.01)
        assert r.correction_total == pytest.approx(0.212, abs=0.01)

    def test_higher_he_increases_hs(self):
        pos = Position(lat=30.0, lon=-40.0)
        dt = datetime(2026, 6, 21, 14, 0, 0, tzinfo=UTC)
        r_low = compute_ho("Sun", dt, pos, 10.0)
        r_high = compute_ho("Sun", dt, pos, 50.0)
        assert r_high.dip_arcmin > r_low.dip_arcmin
        assert r_high.hs > r_low.hs
