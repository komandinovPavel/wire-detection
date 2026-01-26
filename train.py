# import torch

# print(torch.__version__)        # должен быть torch 2.9.x+cu124
# print(torch.version.cuda)       # '12.4'
# print(torch.cuda.is_available())  # True
# print(torch.cuda.device_count())  # >0, сколько GPU у тебя есть

from ultralytics import YOLO

if __name__ == "__main__":
    # Загружаем pre-trained модель сегментации
    model = YOLO("yolov8s-seg.pt")  # можно заменить на yolov8n-seg если GPU слабый

    # Обучение
    model.train(
        data="dataset/data.yaml",       # путь к твоему датасету
        epochs=120,             # больше эпох для мелких дефектов
        imgsz=640,              # увеличиваем размер входа для тонкой проволоки
        batch=16,                # подбираем под GPU (2–4 обычно ок)
        lr0=0.001,              # начальный learning rate
        device=0,               # GPU=0, CPU="cpu"
        workers=0,              # Windows-safe
        project="wire_defects_optimized",
        name="v1",
        augment=True,           # включаем аугментации
        overlap_mask=True,      # для мелких объектов (сегментация)
        patience=20             # early stopping, если нет улучшений
    )
