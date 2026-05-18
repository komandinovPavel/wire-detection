# Архитектура проекта

Краткая карта проекта для быстрого входа в код. Приложение - desktop GUI на Tkinter для поиска дефектов проволоки через YOLOv8 segmentation и измерения диаметра после калибровки.

## Назначение

Пользователь выбирает один из источников кадра:

- изображение с диска;
- захват экрана;
- камера.

Кадр попадает в общий pipeline: `CaptureSource` -> `DefectDetector` -> отображение в `DisplayCanvas` -> список дефектов в `DefectPanel`. Для калибровки и измерений используется отдельный путь через `WireAnalyzer`.

## Точка входа

- `main.py` создает `tk.Tk`, инициализирует `ui.main_window.MainWindow`, подписывает закрытие окна на `app.on_closing()` и запускает `root.mainloop()`.
- Главный координатор приложения - `ui/main_window.py`.

## Основные слои

### UI (`ui/`)

- `MainWindow` связывает все компоненты, хранит состояние режимов, запускает/останавливает источники кадров и вызывает модель.
- `ControlPanel` создает верхнюю панель управления: загрузка изображения, экран, камера, стоп, калибровка, измерение, выбор камеры, confidence slider.
- `DisplayCanvas` отображает BGR `np.ndarray` на Tkinter canvas через PIL/ImageTk. Также хранит чистый кадр `_source_frame`, чтобы измерения делались не по кадру с YOLO/калибровочными оверлеями.
- `DefectPanel` показывает историю найденных дефектов и статистику по классам.

Важно: `MainWindow._capture_loop()` работает в отдельном `threading.Thread`, а confidence читается через кеш `_confidence_cache`, потому что прямое чтение Tkinter widget из фонового потока небезопасно.

### Источники кадров (`capture/`)

Все источники наследуются от `CaptureSource` из `capture/base.py` и имеют единый интерфейс:

- `start()`;
- `stop()`;
- `read_frame() -> np.ndarray`;
- `is_available()`.

Реализации:

- `ImageCapture` загружает статичное изображение через OpenCV.
- `ScreenCapture` делает скриншоты через `mss`; объект `mss` создается внутри `read_frame()`, чтобы избежать ошибок thread-local состояния.
- `CameraCapture` читает кадры из `cv2.VideoCapture`.

Вспомогательные функции для камер находятся в `utils/camera_utils.py`: поиск доступных камер и парсинг индекса из строки combobox.

### Ядро (`core/`)

- `Config` хранит пути, размеры окна, цвета, параметры модели и калибровки.
- `DefectDetector` в `core/model.py` - тонкая обертка над `ultralytics.YOLO`. Загружает модель из `Config.MODEL_PATH`, выполняет inference и возвращает `(annotated_frame, detections)`.
- `WireAnalyzer` в `core/wire_analyzer.py` измеряет диаметр проволоки методами OpenCV: grayscale, blur, Canny, морфология, выделение верхней/нижней границы, сглаживание, расчет диаметра по нормали к центральной линии.
- `WireCalibrator` в `core/calibration.py` хранит `pixels_per_mm` и старую механику калибровки по двум точкам. В текущем UI фактическая калибровка делается кликом по проволоке: `WireAnalyzer.measure_diameter_at_x()` измеряет диаметр в пикселях, затем `px_per_mm = diameter_px / Config.NOMINAL_DIAMETER_MM`.

## Поток обработки изображения

Для статичного изображения:

1. `MainWindow.on_load_image()` открывает file dialog.
2. `ImageCapture.load()` читает картинку.
3. Чистый кадр сохраняется в `DisplayCanvas.set_source_frame()`.
4. `DefectDetector.predict()` запускает YOLO.
5. `DisplayCanvas.update_frame()` показывает annotated frame.
6. `DefectPanel.update_defects()` добавляет найденные bbox/class/confidence в список.

Для камеры и экрана:

1. `on_camera_capture()` или `on_screen_capture()` создает нужный `CaptureSource`.
2. `_start_capture_loop()` запускает daemon-thread.
3. `_capture_loop()` циклически читает кадр, сохраняет чистую копию, гонит YOLO, обновляет canvas и панель дефектов.

## Калибровка и измерение

Калибровка:

1. `on_calibrate()` останавливает текущий capture и просит выбрать изображение.
2. Кадр показывается на canvas, включается `calibration_mode`.
3. Клик по canvas преобразуется в координаты исходного кадра через `DisplayCanvas.display_to_original_coords()`.
4. `_do_calibration()` вызывает `WireAnalyzer.measure_diameter_at_x(image, x)`.
5. `pixels_per_mm` считается от номинального диаметра `Config.NOMINAL_DIAMETER_MM`.
6. На изображение рисуются найденные границы, линия измерения, панель с отклонением и статусом допуска.

Измерение:

1. После калибровки `ControlPanel.enable_measure()` включает кнопку Measure.
2. `on_measure_mode()` включает `measurement_mode`.
3. Клик по проволоке вызывает `_do_measurement()`.
4. Диаметр в пикселях переводится в миллиметры через `self.calibrator.pixels_per_mm`.
5. Результат рисуется поверх чистого кадра, не затирая `_source_frame`.

Пороговые зоны отклонения задаются в `Config.TOLERANCE_OK` и `Config.TOLERANCE_WARN`.

## Модель и данные

- Активный путь модели: `runs/segment/wire_defects/v1/weights/best.pt`.
- Датасет YOLO: `dataset/data.yaml`, `dataset/train`, `dataset/val`.
- Сейчас в `dataset/data.yaml` описан один класс: `defect`.
- Обучение запускается через `train.py`: базовая модель `yolov8s-seg.pt`, `epochs=120`, `imgsz=640`, `batch=16`, `device=0`, `workers=0`.
- Результаты обучения лежат в `runs/segment/...` и `wire_defects_optimized/...`.

## Ключевые зависимости

- `tkinter` - desktop UI.
- `ultralytics` / YOLOv8 - сегментация и детекция дефектов.
- `opencv-python` - камеры, чтение изображений, обработка кадров и отрисовка оверлеев.
- `Pillow` - конвертация кадров для Tkinter.
- `numpy` - работа с кадрами и расчетами.
- `mss` - захват экрана.
- `scipy` - median filter в `WireAnalyzer`.

## Что помнить при изменениях

- Tkinter лучше обновлять из главного потока. Сейчас canvas обновляется из capture thread, это потенциальная зона риска.
- Для измерений всегда использовать чистый кадр из `DisplayCanvas.get_current_frame()`, а не annotated frame.
- `WireCalibrator.calculate_calibration()` по двум точкам почти не используется текущим UI; не принимать его за основной сценарий без проверки.
- В проекте есть mojibake в русских строках/комментариях из-за кодировки, поэтому при правках UI-текстов стоит аккуратно проверить отображение.
- `Config.MODEL_PATH` должен соответствовать реально существующему `best.pt`; README и train.py местами называют разные директории результатов.
## Dear PyGui Migration Snapshot

The project now has a backend-first DPG path in addition to the legacy Tkinter UI.

New layers:

- `domain/`: dataclasses and enums shared by app, services, and UI.
- `services/`: capture switching, detection adapter, frame processing, defect history, and overlay home.
- `app/`: thin `AppController`, shared `AppState`, background `ProcessingRuntime`, and `build_controller()`.
- `ui_dpg/`: Dear PyGui shell, responsive frame viewport, control panel, defect panel, and status bar.

DPG entry point:

```powershell
python main_dpg.py
```

Current DPG MVP:

- load image;
- screen capture;
- camera 0 capture;
- YOLO inference;
- confidence slider;
- responsive frame scaling on window/fullscreen resize;
- defect history and class statistics;
- status display.

Still pending for DPG:

- calibration workflow;
- measurement workflow;
- detailed visual polish after manual smoke testing.
