from domain import Detection
from services.defect_history import DefectHistory


def make_detection(name: str = "defect", confidence: float = 0.75) -> Detection:
    return Detection(class_name=name, confidence=confidence, bbox=(1, 2, 3, 4))


def test_add_updates_total_and_class_counts():
    history = DefectHistory(max_items=10)

    history.add([make_detection("scratch"), make_detection("scratch"), make_detection("crack")])

    stats = history.stats()
    assert stats.total == 3
    assert stats.by_class == {"scratch": 2, "crack": 1}


def test_recent_is_limited_to_max_items_but_total_keeps_growing():
    history = DefectHistory(max_items=2)

    history.add([make_detection("a")])
    history.add([make_detection("b")])
    history.add([make_detection("c")])

    recent = history.recent()
    assert [item.class_name for item in recent] == ["c", "b"]
    assert history.stats().total == 3


def test_clear_resets_history_and_stats():
    history = DefectHistory(max_items=10)
    history.add([make_detection("defect")])

    history.clear()

    assert history.recent() == []
    assert history.stats().total == 0
    assert history.stats().by_class == {}
