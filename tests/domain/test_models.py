from domain import (
    AppMode,
    DefectStats,
    CalibrationResult,
    Detection,
    FrameResult,
    MeasurementResult,
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
    assert settings.yolo_enabled is True


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


def test_measurement_result_derives_deviation_and_tolerance():
    result = MeasurementResult(
        x=120,
        diameter_px=188.0,
        diameter_mm=1.92,
        pixels_per_mm=100.0,
        top_y=10,
        bottom_y=198,
        slope=0.0,
        nominal_diameter_mm=1.88,
        tolerance_ok=0.03,
        tolerance_warn=0.07,
    )

    assert result.deviation_mm == 0.04
    assert result.tolerance_level == "warn"
    assert result.tolerance_label == "WARNING"


def test_calibration_result_exposes_scale_and_measured_diameter():
    result = CalibrationResult(
        x=100,
        calibration_diameter_px=188.0,
        measured_diameter_px=190.0,
        measured_diameter_mm=1.9,
        pixels_per_mm=100.0,
        top_y=10,
        bottom_y=198,
        slope=0.1,
        nominal_diameter_mm=1.88,
        tolerance_ok=0.03,
        tolerance_warn=0.07,
    )

    assert result.deviation_mm == 0.02
    assert result.tolerance_level == "ok"
    assert result.tolerance_label == "IN TOLERANCE"


def test_runtime_snapshot_exposes_status_and_source():
    snapshot = RuntimeSnapshot(
        status=RuntimeStatus.RUNNING,
        source_type=SourceType.CAMERA,
        mode=AppMode.DETECT,
        message="Camera active",
        settings=ProcessingSettings(confidence=0.45),
        stats=DefectStats(total=2, by_class={"defect": 2}),
        measurement_enabled=True,
    )

    assert snapshot.status is RuntimeStatus.RUNNING
    assert snapshot.source_type is SourceType.CAMERA
    assert snapshot.measurement_enabled is True
    assert snapshot.settings.confidence == 0.45
    assert snapshot.stats.by_class["defect"] == 2
