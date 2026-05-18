from domain import Detection
from services.defect_event_filter import DefectEventFilter, bbox_iou


def detection(name="scratch", bbox=(0, 0, 10, 10), timestamp=1.0):
    return Detection(name, 0.9, bbox, timestamp=timestamp)


def test_bbox_iou_returns_overlap_ratio():
    assert bbox_iou((0, 0, 10, 10), (5, 5, 15, 15)) == 25 / 175


def test_first_detection_is_new_event():
    event_filter = DefectEventFilter(iou_threshold=0.4, window_seconds=2.0)

    result = event_filter.filter_new([detection(timestamp=10.0)], now=10.0)

    assert len(result) == 1


def test_same_class_same_area_inside_window_is_not_new_event():
    event_filter = DefectEventFilter(iou_threshold=0.4, window_seconds=2.0)
    event_filter.filter_new([detection(timestamp=10.0)], now=10.0)

    result = event_filter.filter_new([detection(bbox=(1, 1, 11, 11), timestamp=11.0)], now=11.0)

    assert result == []


def test_same_area_after_window_is_new_event():
    event_filter = DefectEventFilter(iou_threshold=0.4, window_seconds=2.0)
    event_filter.filter_new([detection(timestamp=10.0)], now=10.0)

    result = event_filter.filter_new([detection(timestamp=13.1)], now=13.1)

    assert len(result) == 1


def test_different_class_or_far_bbox_is_new_event():
    event_filter = DefectEventFilter(iou_threshold=0.4, window_seconds=2.0)
    event_filter.filter_new([detection("scratch", timestamp=10.0)], now=10.0)

    different_class = event_filter.filter_new([detection("crack", timestamp=10.5)], now=10.5)
    far_bbox = event_filter.filter_new([detection("scratch", bbox=(50, 50, 60, 60), timestamp=10.7)], now=10.7)

    assert len(different_class) == 1
    assert len(far_bbox) == 1
