from domain import SourceType
from ui_dpg.adapters.fps_tracker import FpsTracker


def test_first_live_frame_has_no_fps_sample_yet():
    tracker = FpsTracker(window_seconds=5.0)

    fps = tracker.observe(SourceType.CAMERA, frame_key=object(), now=10.0)

    assert fps is None
    assert tracker.samples == ()


def test_second_live_frame_computes_fps_from_frame_interval():
    tracker = FpsTracker(window_seconds=5.0)
    tracker.observe(SourceType.CAMERA, frame_key=object(), now=10.0)

    fps = tracker.observe(SourceType.CAMERA, frame_key=object(), now=10.04)

    assert round(fps, 1) == 25.0
    assert len(tracker.samples) == 1
    assert round(tracker.samples[0].fps, 1) == 25.0


def test_repeated_same_frame_does_not_create_fake_fps_samples():
    tracker = FpsTracker(window_seconds=5.0)
    frame_key = object()
    tracker.observe(SourceType.CAMERA, frame_key=frame_key, now=10.0)

    fps = tracker.observe(SourceType.CAMERA, frame_key=frame_key, now=10.001)

    assert fps is None
    assert tracker.samples == ()


def test_history_is_limited_to_window_seconds():
    tracker = FpsTracker(window_seconds=1.0)
    tracker.observe(SourceType.CAMERA, frame_key=object(), now=10.0)
    tracker.observe(SourceType.CAMERA, frame_key=object(), now=10.5)
    tracker.observe(SourceType.CAMERA, frame_key=object(), now=11.6)

    assert [sample.timestamp for sample in tracker.samples] == [11.6]


def test_non_live_source_clears_history_and_disables_fps():
    tracker = FpsTracker(window_seconds=5.0)
    tracker.observe(SourceType.CAMERA, frame_key=object(), now=10.0)
    tracker.observe(SourceType.CAMERA, frame_key=object(), now=10.1)

    fps = tracker.observe(SourceType.IMAGE, frame_key=object(), now=11.0)

    assert fps is None
    assert tracker.samples == ()
