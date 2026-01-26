# 🔍 Wire Defect Detector

YOLOv8-based wire defect detection system with GUI for real-time inspection.

---

## 📁 Структура проекта

```
wire_defect_detector/
│
├── main.py                      # 🚀 GUI приложение (запуск детектора)
├── train.py                     # 🎓 Обучение модели YOLO
├── check.py                     # ✅ Проверка работы модели
├── requirements.txt
├── README.md
│
├── wire_dataset/                # 📸 Исходные изображения для обучения
│   ├── image1.jpg
│   ├── image2.jpg
│   └── ...
│
├── dataset/                     # 📊 Подготовленный датасет в формате YOLO
│   ├── data.yaml               # Конфигурация датасета
│   ├── train/
│   │   ├── images/
│   │   └── labels/
│   └── val/
│       ├── images/
│       └── labels/
│
├── runs/                        # 💾 Результаты обучения (создаётся автоматически)
│   └── segment/
│       └── wire_defects/
│           └── v1/
│               └── weights/
│                   └── best.pt  # Лучшая модель после обучения
│
├── core/                        # 🧠 Логика приложения
│   ├── config.py
│   ├── model.py
│   └── calibration.py
│
├── capture/                     # 📹 Источники видео
│   ├── base.py
│   ├── camera.py
│   ├── screen.py
│   └── image.py
│
├── ui/                          # 🎨 Графический интерфейс
│   ├── main_window.py
│   ├── control_panel.py
│   ├── display_canvas.py
│   └── defect_panel.py
│
└── utils/                       # 🛠️ Вспомогательные функции
    └── camera_utils.py
```

---

## 🚀 Быстрый старт

### 1️⃣ Установка зависимостей

```bash
# Создай виртуальное окружение (опционально, но рекомендуется)
python -m venv venv
venv\Scripts\activate  # Windows
# source venv/bin/activate  # Linux/Mac

# Установи PyTorch с CUDA 12.4
pip install torch torchvision torchaudio --index-url https://download.pytorch.org/whl/cu124

# Установи остальные зависимости
pip install ultralytics opencv-python pillow numpy mss scipy
```

**Проверка установки:**
```bash
python -c "import torch; print('PyTorch:', torch.__version__); print('CUDA:', torch.cuda.is_available())"
```
Должно вывести: `PyTorch: 2.x.x+cu124` и `CUDA: True`

---

### 2️⃣ Подготовка датасета

Убедись что структура датасета правильная:

```
dataset/
├── data.yaml          # Конфигурация (пути, классы)
├── train/
│   ├── images/       # Изображения для обучения
│   └── labels/       # Аннотации в формате YOLO
└── val/
    ├── images/       # Изображения для валидации
    └── labels/       # Аннотации для валидации
```

**Пример `data.yaml`:**
```yaml
path: ./dataset
train: train/images
val: val/images

nc: 3  # Количество классов дефектов
names: ['crack', 'scratch', 'bend']  # Названия классов
```

---

### 3️⃣ Обучение модели

```bash
python train.py
```

**Что происходит:**
- Загружается pre-trained модель `yolov8s-seg.pt`
- Обучение на 120 эпох
- Результаты сохраняются в `wire_defects_optimized/v1/`
- Лучшая модель: `wire_defects_optimized/v1/weights/best.pt`

**Параметры обучения (в `train.py`):**
```python
epochs=120           # Количество эпох
imgsz=640           # Размер изображения
batch=16            # Размер батча (уменьши если мало VRAM)
lr0=0.001           # Learning rate
device=0            # GPU (или "cpu")
patience=20         # Early stopping
```

---

### 4️⃣ Проверка модели

```bash
python check.py
```

Скрипт должен:
- Загрузить обученную модель
- Запустить inference на тестовых изображениях
- Показать результаты

---

### 5️⃣ Обновление пути к модели

После обучения обнови путь к модели в `core/config.py`:

```python
# core/config.py

class Config:
    # Укажи путь к твоей обученной модели
    MODEL_PATH = "wire_defects_optimized/v1/weights/best.pt"
    # или
    # MODEL_PATH = "runs/segment/wire_defects/v1/weights/best.pt"
```

---

### 6️⃣ Запуск GUI приложения

```bash
python main.py
```

**Возможности GUI:**
- 📁 **Load Image** - загрузить фото для анализа
- 🖥️ **Screen** - захват экрана в реальном времени
- 📷 **Camera** - захват с веб-камеры
- 📏 **Calibrate** - калибровка для измерения размеров
- 🔍 **Defect Panel** - список найденных дефектов

---

## 🎯 Workflow

### Полный цикл работы:

```
1. Подготовка датасета
   └─> wire_dataset/ → dataset/ (с аннотациями)

2. Обучение
   └─> python train.py
   └─> Результат: wire_defects_optimized/v1/weights/best.pt

3. Проверка
   └─> python check.py

4. Обновление config.py
   └─> MODEL_PATH = "путь/к/best.pt"

5. Запуск GUI
   └─> python main.py
```

---

## 📏 Калибровка (в GUI)

### Как откалибровать систему:

1. **Нажми** "📏 Calibrate"
2. **Выбери** изображение с проволокой
3. **Кликни** по двум точкам известного расстояния  
   (например, начало и конец проволоки длиной 50мм)
4. **Введи** реальное расстояние в мм
5. **Получи:**
   - Калибровку: `12.456 px/mm`
   - Диаметр проволоки: `3.214 mm`

Теперь все измерения будут в реальных единицах!

---

## 🔧 Параметры и настройки

### Изменить модель YOLO

В `train.py` можно использовать другие модели:
```python
model = YOLO("yolov8n-seg.pt")  # Nano - быстрая, но менее точная
model = YOLO("yolov8s-seg.pt")  # Small - баланс (по умолчанию)
model = YOLO("yolov8m-seg.pt")  # Medium - точнее, но медленнее
model = YOLO("yolov8l-seg.pt")  # Large - максимальная точность
```

### Изменить confidence threshold

В GUI двигай ползунок **Confidence** (0.1 - 0.9)

Или в `core/config.py`:
```python
DEFAULT_CONFIDENCE = 0.3  # Порог уверенности (0-1)
```

### Изменить размер входа

В `core/config.py`:
```python
DEFAULT_IMGSZ = 640  # 640, 1024, 1280 (больше = точнее, но медленнее)
```

---


## 📊 Мониторинг обучения

Во время обучения можно отслеживать метрики:

```bash
# TensorBoard (если установлен)
tensorboard --logdir wire_defects_optimized

# Или смотри логи в консоли и файлы в:
wire_defects_optimized/v1/
├── weights/
│   ├── best.pt       # Лучшая модель
│   └── last.pt       # Последняя эпоха
├── results.csv       # Метрики по эпохам
└── *.png            # Графики обучения
```

---

## 🎓 Дополнительные материалы

- [Ultralytics YOLOv8 Docs](https://docs.ultralytics.com/)
- [YOLO Segmentation Guide](https://docs.ultralytics.com/tasks/segment/)
- [Dataset Format](https://docs.ultralytics.com/datasets/segment/)

---

## 📝 TODO / Roadmap

- [ ] Экспорт результатов в CSV/JSON
- [ ] Сохранение обработанных изображений
- [ ] История калибровок
- [ ] Batch processing для папок с изображениями
- [ ] REST API для интеграции
- [ ] Docker контейнер

---

## 💡 Tips & Tricks

### Ускорение обучения
- Уменьши `batch` если не хватает VRAM
- Используй `workers=4` на Linux (на Windows оставь 0)
- Уменьши `imgsz` до 320-480 для быстрого экспериментирования

### Улучшение точности
- Больше данных (>500 изображений)
- Data augmentation (уже включен)
- Больше эпох (150-200)
- Используй yolov8m-seg или yolov8l-seg

### Калибровка
- Используй линейку в кадре для точной калибровки
- Калибруйся каждый раз при смене камеры/расстояния
- Сохраняй значение px/mm для повторного использования

---

## 🤝 Contributing

Pull requests приветствуются! Для больших изменений сначала откройте issue.

---

## 📄 License

MIT License - используй как хочешь! 🎉

---

## 🚀 Готово к запуску!

```bash
python main.py
```

Удачной детекции дефектов! 🔍✨