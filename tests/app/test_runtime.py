import threading

import numpy as np

from app.runtime import ProcessingRuntime
from app.state import AppState
from domain import FrameResult, RuntimeStatus


class OneFrameCapture:
    def __init__(self):
        self.frames = [np.zeros((2, 2, 3), dtype=np.uint8)]
        self.stopped = False

    def read_frame(self):
        if self.frames:
            return self.frames.pop()
        return None

    def stop(self):
        self.stopped = True


class RecordingProcessor:
    def __init__(self):
        self.calls = 0

    def process(self, frame, settings):
        self.calls += 1
        return FrameResult(
            source_frame=frame,
            display_frame=frame,
            status=RuntimeStatus.READY,
            message="processed",
        )


def test_run_once_processes_frame_and_stores_latest_result():
    capture = OneFrameCapture()
    processor = RecordingProcessor()
    runtime = ProcessingRuntime(capture, processor, AppState())

    processed = runtime.run_once()

    assert processed is True
    assert processor.calls == 1
    assert runtime.poll_latest().message == "processed"


def test_run_once_returns_false_when_no_frame_available():
    capture = OneFrameCapture()
    capture.frames.clear()
    runtime = ProcessingRuntime(capture, RecordingProcessor(), AppState())

    processed = runtime.run_once()

    assert processed is False
    assert runtime.poll_latest() is None


class BlockingCapture:
    def __init__(self):
        self.first_read_started = threading.Event()
        self.release_first_read = threading.Event()
        self.read_calls = 0

    def read_frame(self):
        self.read_calls += 1
        if self.read_calls == 1:
            self.first_read_started.set()
            self.release_first_read.wait(timeout=1.0)
        return None


def test_start_waits_for_previous_loop_before_clearing_stop_event():
    capture = BlockingCapture()
    runtime = ProcessingRuntime(capture, RecordingProcessor(), AppState(), interval_s=0.001)
    runtime.start()
    assert capture.first_read_started.wait(timeout=1.0)

    restart = threading.Thread(target=runtime.start)
    restart.start()
    assert restart.is_alive()

    capture.release_first_read.set()
    restart.join(timeout=1.0)

    assert not restart.is_alive()
    runtime.stop()


class StillAliveThread:
    def __init__(self):
        self.join_timeout = None

    def is_alive(self):
        return True

    def join(self, timeout=None):
        self.join_timeout = timeout


def test_stop_keeps_live_thread_reference_when_join_times_out():
    runtime = ProcessingRuntime(OneFrameCapture(), RecordingProcessor(), AppState(), stop_timeout_s=0.01)
    thread = StillAliveThread()
    runtime._thread = thread

    try:
        runtime.stop(join=True)
    except RuntimeError as exc:
        assert str(exc) == "Processing runtime did not stop within timeout"
    else:
        raise AssertionError("Expected stop() to raise when runtime thread stays alive")

    assert runtime._thread is thread
    assert thread.join_timeout == 0.01


def test_start_does_not_launch_second_loop_when_previous_thread_cannot_stop():
    runtime = ProcessingRuntime(OneFrameCapture(), RecordingProcessor(), AppState(), stop_timeout_s=0.01)
    thread = StillAliveThread()
    runtime._thread = thread

    try:
        runtime.start()
    except RuntimeError as exc:
        assert str(exc) == "Processing runtime did not stop within timeout"
    else:
        raise AssertionError("Expected start() to propagate stop timeout")

    assert runtime._thread is thread
    assert runtime._stop_event.is_set()
