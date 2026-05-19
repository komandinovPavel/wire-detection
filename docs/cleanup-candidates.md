# Уборка файлов

Документ фиксирует, что уже убрано, что перенесено, и какие generated artifacts пока остаются кандидатами на удаление.

## Сделано

- `new2.py` удален как экспериментальный OpenCV/Tkinter pipeline.
- `test.py` удален как ручной черновой скрипт, не pytest-тест.
- `check.py` перенесен и отрефакторен в `utils/check_environment.py`.
- `yolo_test.py` перенесен и отрефакторен в `utils/validate_yolo_dataset.py`.
- `yolov8n-seg.pt` и `yolov8s-seg.pt` перенесены в `weights/base/`.
- `utils/camera_utils.py` подключен к `CaptureService`; раньше рабочий код его не использовал.

## Оставить

- `wire_dataset/` - исходные изображения оставляем.
- `runs/segment/wire_defects/v1/weights/best.pt` - сейчас это активная модель из `Config.MODEL_PATH`.
- `dataset/` - основной YOLO dataset.
- `docs/superpowers/` - исторический контекст миграции; там есть устаревшие упоминания Tkinter и `main_dpg.py`, но они описывают прошлые этапы.

## Кандидаты на удаление позже

- `runs/segment/val4/` - результат валидации/эксперимента, вероятно generated artifact.
- `runs/segment/wire_defects_optimized/v1/` и `runs/segment/wire_defects_optimized/v12/` - старые/альтернативные training runs. Удалять только после выбора канонической модели.
