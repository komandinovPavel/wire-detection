#Выбор изображения

import cv2
import numpy as np
import matplotlib.pyplot as plt
from tkinter import Tk
from tkinter.filedialog import askopenfilename


def select_image():

    Tk().withdraw()
    file_path = askopenfilename(
        title="Выберите изображение проволоки",
        filetypes=[
            ("Image files", "*.jpg *.png *.bmp *.tif"),
            ("All files", "*.*")
        ]
    )
    if not file_path:
        raise ValueError("Изображение не выбрано")
    return file_path


def preprocess_image(image_path):
    # Загрузка
    img = cv2.imread(image_path)
    if img is None:
        raise IOError("Не удалось загрузить изображение")

    img_rgb = cv2.cvtColor(img, cv2.COLOR_BGR2RGB)
    gray = cv2.cvtColor(img, cv2.COLOR_BGR2GRAY)
    blur = cv2.GaussianBlur(gray, (5, 5), 0)

    return img_rgb, gray, blur


def show_results(img_rgb, gray, blur):
    plt.figure(figsize=(15, 5))

    plt.subplot(1, 3, 1)
    plt.title("Исходное изображение")
    plt.imshow(img_rgb)
    plt.axis("off")

    plt.subplot(1, 3, 2)
    plt.title("Градации серого")
    plt.imshow(gray, cmap="gray")
    plt.axis("off")

    plt.subplot(1, 3, 3)
    plt.title("После гауссовой фильтрации")
    plt.imshow(blur, cmap="gray")
    plt.axis("off")

    plt.tight_layout()
    plt.show()

#Детекция
def detect_edges(blur):

    # Пороги подобраны под текущее изображение
    edges = cv2.Canny(
        blur,
        threshold1=50,
        threshold2=150
    )
    return edges

def show_edges(edges):
    plt.figure(figsize=(10, 3))
    plt.title("Выделенные границы (Canny)")
    plt.imshow(edges, cmap="gray")
    plt.axis("off")
    plt.show()
#Диаметр

def extract_wire_edges(edges):
    height, width = edges.shape
    xs = []
    top_y = []
    bottom_y = []

    for x in range(width):
        column = edges[:, x]
        ys = np.where(column > 0)[0]

        if len(ys) > 1:
            xs.append(x)
            top_y.append(ys[0])
            bottom_y.append(ys[-1])

    return np.array(xs), np.array(top_y), np.array(bottom_y)


def compute_centerline(top_y, bottom_y):

    center_y = (top_y + bottom_y) / 2.0
    return center_y


def measure_diameter_normal(top_y, bottom_y, center_y):


    # Производная центральной линии
    d_center_dx = np.gradient(center_y)

    # Коэффициент перехода к нормали
    normal_factor = 1.0 / np.sqrt(1.0 + d_center_dx**2)

    # Вертикальный диаметр
    diameter_vertical = bottom_y - top_y

    # Диаметр по нормали
    diameter_normal = diameter_vertical * normal_factor

    return diameter_normal


def smooth_signal(signal, kernel_size=21):
    kernel = np.ones(kernel_size) / kernel_size
    return np.convolve(signal, kernel, mode='same')


def robust_diameter(diameters, k=2.0):

    diameters = np.array(diameters)

    median = np.median(diameters)
    mad = np.median(np.abs(diameters - median))

    if mad == 0:
        return diameters

    lower = median - k * mad
    upper = median + k * mad

    filtered = diameters[(diameters >= lower) & (diameters <= upper)]

    return filtered


calibration_points = []
fixed_x = None


def mouse_callback(event, x, y, flags, param):

    global calibration_points, fixed_x

    if event == cv2.EVENT_LBUTTONDOWN:
        if len(calibration_points) == 0:
            fixed_x = x
            calibration_points.append((x, y))
            print(f"Первая точка: ({x}, {y})")
        elif len(calibration_points) == 1:
            calibration_points.append((fixed_x, y))
            print(f"Вторая точка (привязана по X): ({fixed_x}, {y})")


def calibrate_scale(img_rgb, real_diameter_mm):

    global calibration_points, fixed_x
    calibration_points = []
    fixed_x = None

    img_bgr = cv2.cvtColor(img_rgb.copy(), cv2.COLOR_RGB2BGR)

    window_name = "Калибровка: кликни верх и низ проволоки"
    cv2.namedWindow(window_name)
    cv2.setMouseCallback(window_name, mouse_callback)

    while True:
        temp = img_bgr.copy()
        h, w, _ = temp.shape

        step = 20
        for i in range(0, w, step):
            cv2.line(temp, (i, 0), (i, h), (70, 70, 70), 1)
        for i in range(0, h, step):
            cv2.line(temp, (0, i), (w, i), (70, 70, 70), 1)

        #Направляющая
        if fixed_x is not None:
            cv2.line(temp, (fixed_x, 0), (fixed_x, h), (0, 255, 0), 1)

        for p in calibration_points:
            cv2.circle(temp, p, 6, (0, 0, 255), -1)

        cv2.imshow(window_name, temp)

        if len(calibration_points) == 2:
            break

        if cv2.waitKey(1) & 0xFF == 27:  # ESC
            cv2.destroyAllWindows()
            raise RuntimeError("Калибровка отменена")

    cv2.destroyAllWindows()

    #Расчет масштаба
    p1, p2 = calibration_points
    pixel_distance = abs(p2[1] - p1[1])

    scale_mm_per_pixel = real_diameter_mm / pixel_distance

    print(f"Расстояние в пикселях: {pixel_distance:.2f}")
    print(f"Масштаб: {scale_mm_per_pixel:.6f} мм/пиксель")

    return scale_mm_per_pixel






if __name__ == "__main__":

    image_path = select_image()
    img_rgb, gray, blur = preprocess_image(image_path)
    show_results(img_rgb, gray, blur)

    edges = detect_edges(blur)
    show_edges(edges)

    xs, top_y, bottom_y = extract_wire_edges(edges)

    # центр
    center_y = (top_y + bottom_y) / 2

    # сглаживание центра
    center_y_smooth = smooth_signal(center_y)

    # производная центра
    d_center_dx = np.gradient(center_y_smooth)

    # коэффициент перехода к нормали
    normal_factor = 1.0 / np.sqrt(1.0 + d_center_dx ** 2)

    # вертикальный диаметр
    diameter_vertical = bottom_y - top_y

    diameters_px = diameter_vertical * normal_factor

    plt.figure(figsize=(10, 4))
    plt.plot(diameters_px, linewidth=1)
    plt.title("Диаметр проволоки по столбцам (в пикселях)")
    plt.xlabel("Номер столбца")
    plt.ylabel("Диаметр, пиксели")
    plt.grid(True)
    plt.show()

    diameters_filtered = robust_diameter(diameters_px)

    print(f"Фильтрованный средний диаметр (px): {np.mean(diameters_filtered):.2f}")
    print(f"Фильтрованная медиана (px): {np.median(diameters_filtered):.2f}")

    real_diameter_mm = 1.88
    scale = calibrate_scale(img_rgb, real_diameter_mm)

    diameter_mm = np.mean(diameters_filtered) * scale
    print(f"Итоговый диаметр: {diameter_mm:.3f} мм")
