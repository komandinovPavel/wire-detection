# Архитектура проекта

Краткая карта проекта для быстрого входа в код. Приложение - desktop GUI на Dear PyGui для поиска дефектов проволоки через YOLOv8 segmentation, ведения истории дефектов, калибровки и измерения диаметра.

## Назначение

Пользователь выбирает один из источников кадра:

- изображение с диска;
- захват экрана;
- камера.

Кадр проходит через общий backend pipeline:

`CaptureSource` -> `CaptureService` -> `FrameProcessor` -> `DetectionService` -> `FrameResult` -> `ui_dpg`.

Калибровка и измерения идут через `AppController`, `CalibrationService`, `WireAnalyzer` и `MeasurementOverlay`. UI не содержит OpenCV-математику и не вызывает YOLO напрямую.

## Точки входа

- `main.py` - основной запуск приложения, делегирует в Dear PyGui UI.
- `ui_dpg/app.py` создает DPG context, viewport, главное окно, модальные окна, update loop и связывает UI с `AppController`.

## Основные слои

### Domain (`domain/`)

Слой явных контрактов между приложением, сервисами и UI.

- `Detection` - нормализованная детекция с bbox, class name и confidence.
- `FrameResult` - результат обработки кадра: отображаемый кадр, чистый кадр, текущие и новые детекции, статистика, время обработки.
- `ProcessingSettings` - confidence, размер входа YOLO, флаги дедупликации и включения YOLO.
- `RuntimeSnapshot` - состояние приложения для UI.
- `SourceType`, `AppMode`, `RuntimeStatus` - перечисления статуса, режима и источника.

Domain не зависит от OpenCV, YOLO, Dear PyGui или capture-реализаций.

### Services (`services/`)

Backend use cases и переиспользуемая логика.

- `DetectionService` - typed adapter над `core.model.DefectDetector`.
- `CaptureService` - создает и переключает image/screen/camera sources, останавливает текущий source, ищет камеры.
- `FrameProcessor` - обрабатывает один кадр с текущими настройками и обновляет историю только новыми событиями.
- `DefectEventFilter` - дедуплицирует стабильные live-детекции по классу, bbox IoU и временному окну.
- `DefectHistory` - хранит историю дефектов и статистику по классам.
- `CalibrationService` - считает `px/mm` по клику на проволоке и выполняет измерения после калибровки.
- `MeasurementOverlay` - рисует калибровочные и измерительные оверлеи на BGR кадрах.
- `OverlayService` - место для расширения overlay-логики.

Services могут зависеть от `domain`, `core` и `capture`, но не от UI framework.

### App (`app/`)

Тонкий orchestration слой между UI и backend.

- `AppController` - facade для UI: загрузить изображение, запустить экран/камеру, остановить source, поменять настройки, очистить вывод, загрузить калибровочное изображение, включить измерение.
- `ProcessingRuntime` - background loop для live-источников и тестируемый one-frame path `run_once()`.
- `AppState` - текущие настройки, выбранный source, режим, статус и состояние измерения.
- `build_controller()` - composition root: собирает config, detector, services, runtime и controller.

`AppController` должен оставаться тонким: он координирует сценарии, но не содержит YOLO inference, OpenCV capture, drawing или расчетов.

### UI (`ui_dpg/`)

Dear PyGui интерфейс.

- `app.py` - жизненный цикл DPG приложения, layout resize, file dialogs, polling результатов.
- `views/control_panel.py` - источники, камера, confidence, действия, settings, measurement toggle.
- `views/settings_window.py` - runtime настройки, включая YOLO enable/disable и дедупликацию.
- `views/calibration_window.py` - загрузка калибровочного кадра и click-to-calibrate.
- `views/viewport.py` - responsive отображение кадров через DPG texture и преобразование координат клика в координаты исходного кадра.
- `views/defects_panel.py` - таблица новых дефектов и статистика.
- `views/status_bar.py` - статус, source badge, mode, YOLO state, measurement state, FPS и sparkline.
- `adapters/frame_texture.py` - конвертация BGR `np.ndarray` в texture data.
- `adapters/status_metrics.py` и `adapters/fps_tracker.py` - форматирование статусов и live FPS.

UI вызывает только `AppController` и работает с `domain`-объектами. Tkinter UI удален; файловые диалоги реализованы средствами Dear PyGui.

### Источники кадров (`capture/`)

Все источники наследуются от `CaptureSource` из `capture/base.py` и имеют единый интерфейс:

- `start()`;
- `stop()`;
- `read_frame() -> np.ndarray`;
- `is_available()`.

Реализации:

- `ImageCapture` загружает статичное изображение через OpenCV.
- `ScreenCapture` делает скриншоты через `mss`.
- `CameraCapture` читает кадры из `cv2.VideoCapture`.

Вспомогательные функции для камер находятся в `utils/camera_utils.py`.

### Core (`core/`)

- `Config` хранит пути, размеры окна, параметры модели, параметры UI и калибровки.
- `DefectDetector` в `core/model.py` - тонкая обертка над `ultralytics.YOLO`.
- `WireAnalyzer` в `core/wire_analyzer.py` измеряет диаметр проволоки методами OpenCV.
- `WireCalibrator` в `core/calibration.py` хранит `pixels_per_mm` и старую механику калибровки по двум точкам; основной DPG сценарий использует `CalibrationService`.

## Потоки обработки

### Статичное изображение

1. UI открывает DPG file dialog.
2. `AppController.load_image(path)` останавливает live source и очищает stale live frame.
3. `CaptureService` загружает кадр через `ImageCapture`.
4. `FrameProcessor` применяет YOLO, если он включен.
5. `ui_dpg` показывает `FrameResult.display_frame`.
6. `DefectsPanelView` добавляет только `FrameResult.new_detections`, статистика приходит из `FrameResult.stats`.

### Камера и экран

1. UI вызывает `AppController.start_camera(index)` или `start_screen()`.
2. `ProcessingRuntime.start()` останавливает старый worker и запускает background loop.
3. Runtime читает кадры из активного `CaptureSource`.
4. `FrameProcessor` возвращает текущие детекции и новые события.
5. UI polling забирает последний `FrameResult`, обновляет viewport, defect table, status bar и FPS.

### Калибровка и измерение

1. UI открывает calibration window.
2. DPG file dialog загружает чистый calibration frame через `AppController.load_calibration_image(path)`.
3. Клик по preview переводится из display coords в source coords внутри `ViewportView`.
4. `AppController.calibrate_at(x)` вызывает `CalibrationService`.
5. `CalibrationService` измеряет диаметр в пикселях через `WireAnalyzer.measure_diameter_at_x()` и считает `pixels_per_mm = diameter_px / Config.NOMINAL_DIAMETER_MM`.
6. `MeasurementOverlay` рисует результат калибровки.
7. После калибровки measurement toggle становится доступен.
8. При измерении `AppController.start_measurement_mode()` фиксирует чистый кадр, `measure_at(x)` считает диаметр и возвращает overlay.

## Модель и данные

- Активный путь модели: `runs/segment/wire_defects/v1/weights/best.pt`.
- Базовые скачанные веса для обучения лежат в `weights/base/`.
- Датасет YOLO: `dataset/data.yaml`, `dataset/train`, `dataset/val`.
- В `dataset/data.yaml` сейчас описан один класс: `defect`.
- Обучение запускается через `train.py`.
- Результаты обучения лежат в `runs/segment/...` и `wire_defects_optimized/...`, если скрипт обучения запускался с project вне `runs`.

## Ключевые зависимости

- `dearpygui` - desktop UI.
- `ultralytics` / YOLOv8 - сегментация и детекция дефектов.
- `opencv-python` - камеры, чтение изображений, обработка кадров и отрисовка оверлеев.
- `numpy` - работа с кадрами и расчетами.
- `mss` - захват экрана.
- `scipy` - median filter в `WireAnalyzer`.

## Что помнить при изменениях

- Backend не должен зависеть от Dear PyGui или других UI frameworks.
- UI не должен напрямую вызывать YOLO, OpenCV capture sources или measurement math.
- Для измерений использовать clean frame, а не annotated frame.
- `ProcessingRuntime.clear_latest()` нужен, чтобы остановленный live stream не перерисовал UI после загрузки изображения.
- `FrameResult.detections` - все текущие детекции на кадре, `FrameResult.new_detections` - события, которые добавляются в историю.
- `ProcessingSettings.yolo_enabled=False` должен оставлять рендер кадров рабочим, но не добавлять детекции и счетчики.
- `Config.MODEL_PATH` должен соответствовать реально существующему `best.pt`.
