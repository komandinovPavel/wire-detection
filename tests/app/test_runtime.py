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
