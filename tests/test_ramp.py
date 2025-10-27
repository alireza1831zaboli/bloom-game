from app.settings import MAX_PHASE, RAMP_DURATION


def smoothstep(t: float) -> float:
    t = max(0.0, min(1.0, t))
    return t * t * (3 - 2 * t)


def test_smoothstep_monotonic():
    last = -1
    for i in range(0, 101):
        v = smoothstep(i / 100)
        assert v >= last
        last = v


def test_phase_cap():
    assert MAX_PHASE <= 10


def test_ramp_duration_reasonable():
    # sanity: 0.5 -> midpoint should be half-ish but < 0.6 for smoothstep
    mid = smoothstep(0.5)
    assert 0.4 < mid < 0.6
    assert RAMP_DURATION >= 60
