from ui_dpg.adapters.status_metrics import sparkline_points


def test_sparkline_points_normalize_fps_into_drawlist_coordinates():
    points = sparkline_points([0.0, 30.0, 60.0], width=120, height=24, max_fps=60.0)

    assert points == [(0.0, 24.0), (60.0, 12.0), (120.0, 0.0)]


def test_sparkline_points_clamp_values_to_fixed_fps_range():
    points = sparkline_points([-10.0, 120.0], width=100, height=20, max_fps=60.0)

    assert points == [(0.0, 20.0), (100.0, 0.0)]


def test_sparkline_points_require_at_least_two_samples():
    assert sparkline_points([25.0], width=120, height=24, max_fps=60.0) == []
