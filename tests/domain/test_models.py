from domain import (
    AppMode,
    DefectStats,
    Detection,
    FrameResult,
    ProcessingSettings,
    RuntimeSnapshot,
    RuntimeStatus,
    SourceType,
)


def test_processing_settings_defaults_match_existing_config_values():
    settings = ProcessingSettings()

    assert settings.confidence == 0.3
    assert settings.imgsz == 640
    assert settings.deduplicate_defects is True


def test_detection_bbox_is_normalized_to_tuple():
    detection = Detection(class_name="defect", confidence=0.8, bbox=[1, 2, 3, 4])

    assert detection.bbox == (1.0, 2.0, 3.0, 4.0)


def test_frame_result_error_factory_sets_error_status():
    result = FrameResult.error("camera failed")

    assert result.status == RuntimeStatus.ERROR
    assert result.error == "camera failed"
    assert result.detections == []


def test_frame_result_separates_current_detections_from_new_events():
    current = [Detection("scratch", 0.9, (1, 1, 10, 10))]
    new_events = [Detection("scratch", 0.9, (1, 1, 10, 10))]

    result = FrameResult(detections=current, new_detections=new_events)

    assert result.detections is current
    assert result.new_detections is new_events


def test_runtime_snapshot_exposes_status_and_source():
    snapshot = RuntimeSnapshot(
        status=RuntimeStatus.RUNNING,
        source_type=SourceType.CAMERA,
        mode=AppMode.DETECT,
        message="Camera active",
        settings=ProcessingSettings(confidence=0.45),
        stats=DefectStats(total=2, by_class={"defect": 2}),
    )

    assert snapshot.status is RuntimeStatus.RUNNING
    assert snapshot.source_type is SourceType.CAMERA
    assert snapshot.settings.confidence == 0.45
    assert snapshot.stats.by_class["defect"] == 2
