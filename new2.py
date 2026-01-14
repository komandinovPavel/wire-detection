import cv2
import numpy as np
import tkinter as tk
from tkinter import filedialog
import os

# Глобальные переменные
points = []
scale_factor = 1
img_display = None

# Обработчик кликов
def click_event_scaled(event, x, y, flags, param):
    global points, img_display
    if event == cv2.EVENT_LBUTTONDOWN:
        orig_x = int(x / scale_factor)
        orig_y = int(y / scale_factor)
        points.append((orig_x, orig_y))
        cv2.circle(img_display, (orig_x, orig_y), 5, (0, 0, 255), -1)
        resized = cv2.resize(img_display, (int(img_display.shape[1]*scale_factor), int(img_display.shape[0]*scale_factor)))
        cv2.imshow("Select Points on Binary Image", resized)
        print(f"Точка выбрана: ({orig_x}, {orig_y})")
        if len(points) == 2:
            cv2.destroyWindow("Select Points on Binary Image")

# Калибровка на бинарном изображении
def calibrate(binary_img, original_path):
    global img_display, points
    points = []

    img_display = cv2.cvtColor(binary_img, cv2.COLOR_GRAY2BGR)
    resized = cv2.resize(img_display, (int(img_display.shape[1]*scale_factor), int(img_display.shape[0]*scale_factor)))

    print("\nКликните по двум точкам известного отрезка НА БИНАРНОМ ИЗОБРАЖЕНИИ")
    cv2.imshow("Select Points on Binary Image", resized)
    cv2.setMouseCallback("Select Points on Binary Image", click_event_scaled)
    cv2.waitKey(0)
    cv2.destroyAllWindows()

    if len(points) != 2:
        raise ValueError("Не выбраны две точки!")

    p1, p2 = points
    pixel_dist = np.hypot(p2[0]-p1[0], p2[1]-p1[1])
    real_mm = float(input("Реальное расстояние в мм: "))
    pixels_per_mm = pixel_dist / real_mm
    print(f"Калибровка: {pixels_per_mm:.3f} px/мм")
    return pixels_per_mm

# Бинаризация
def binarize_image(img_gray):
    _, binary = cv2.threshold(img_gray, 0, 255, cv2.THRESH_BINARY + cv2.THRESH_OTSU)
    return binary

# Измерение диаметра
def measure_wire_diameter(binary_img, pixels_per_mm, visualize=True):
    contours, _ = cv2.findContours(binary_img, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_NONE)
    if not contours:
        raise RuntimeError("Проволока не найдена")
    wire_contour = max(contours, key=cv2.contourArea)
    mask = np.zeros_like(binary_img)
    cv2.drawContours(mask, [wire_contour], -1, 255, -1)

    dist = cv2.distanceTransform(mask, cv2.DIST_L2, cv2.DIST_MASK_PRECISE)
    _, max_val, _, max_loc = cv2.minMaxLoc(dist)

    x, y = max_loc
    diameter_px = max_val * 2
    diameter_mm = diameter_px / pixels_per_mm

    if visualize:
        vis = cv2.cvtColor(binary_img, cv2.COLOR_GRAY2BGR)
        cv2.circle(vis, (x, y), 5, (0, 0, 255), -1)
        r = int(diameter_px / 2)
        cv2.circle(vis, (x, y), r, (0, 255, 0), 2)
        cv2.putText(vis, f"Diam: {diameter_mm:.3f} mm", (10, 30),
                    cv2.FONT_HERSHEY_SIMPLEX, 1, (255, 255, 0), 2)
        cv2.imshow("Wire Diameter", vis)
        cv2.waitKey(0)
        cv2.destroyAllWindows()

    return diameter_mm, diameter_px

# Детекция дефектов
def detect_defects(binary_img, pixels_per_mm):
    # Для дефектов: инвертируем бинарное
    inv = cv2.bitwise_not(binary_img)
    contours, _ = cv2.findContours(binary_img, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)
    wire_contour = max(contours, key=cv2.contourArea)
    mask_wire = np.zeros_like(binary_img)
    cv2.drawContours(mask_wire, [wire_contour], -1, 255, -1)

    defects_mask = cv2.bitwise_and(inv, inv, mask=mask_wire)
    defect_contours, _ = cv2.findContours(defects_mask, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)

    vis = cv2.cvtColor(binary_img, cv2.COLOR_GRAY2BGR)
    measurements = []
    for i, cnt in enumerate(defect_contours):
        area_px = cv2.contourArea(cnt)
        if area_px < 5: continue
        x, y, w, h = cv2.boundingRect(cnt)
        cv2.rectangle(vis, (x,y), (x+w,y+h), (0,255,0), 1)
        cv2.putText(vis, f"D{i+1}", (x, y-5), cv2.FONT_HERSHEY_SIMPLEX, 0.6, (0,255,0), 1)
        measurements.append({
            "id": i+1,
            "area_mm2": area_px / (pixels_per_mm**2),
            "width_mm": w / pixels_per_mm,
            "height_mm": h / pixels_per_mm
        })

    return vis, measurements

# Выбор файла
def select_image():
    root = tk.Tk()
    root.withdraw()
    file_path = filedialog.askopenfilename(
        title="Выберите изображение",
        filetypes=[("Изображения", "*.jpg *.jpeg *.png *.bmp *.tif"), ("Все файлы", "*.*")]
    )
    return file_path if file_path else None

# Главная функция
def pipeline():
    print("=== Пайплайн анализа проволоки (бинарное изображение сразу) ===")
    print("1. Выберите изображение")
    print("2. Увидите бинарное изображение → кликните по двум точкам")
    print("3. Введите расстояние → получите результат\n")

    while True:
        image_path = select_image()
        if not image_path:
            print("Выход")
            break
        print(f"Выбрано: {image_path}")

        try:

            img = cv2.imread(image_path, cv2.IMREAD_GRAYSCALE)
            binary_img = binarize_image(img)


            cv2.imshow("Binary Image (для калибровки)", binary_img)
            cv2.waitKey(500)  # небольшая пауза
            cv2.destroyWindow("Binary Image (для калибровки)")

            pixels_per_mm = calibrate(binary_img, image_path)
            diameter_mm, diameter_px = measure_wire_diameter(binary_img, pixels_per_mm)
            vis_defects, defects = detect_defects(binary_img, pixels_per_mm)

            print("\n" + "="*60)
            print(f"Диаметр: {diameter_mm:.3f} мм ({diameter_px:.1f} px)")
            print(f"Найдено дефектов: {len(defects)}")
            for d in defects:
                print(f"Дефект {d['id']}: {d['width_mm']:.3f}×{d['height_mm']:.3f} мм, площадь {d['area_mm2']:.4f} мм²")
            print("="*60)

            cv2.imshow("Результат: Дефекты", vis_defects)
            cv2.waitKey(0)
            cv2.destroyAllWindows()

            again = input("\nЕщё одно изображение? (y/n): ").strip().lower()
            if again != 'y':
                break

        except Exception as e:
            print(f"Ошибка: {e}")
            continue

if __name__ == "__main__":
    pipeline()