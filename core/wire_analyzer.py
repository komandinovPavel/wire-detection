import cv2
import numpy as np
from scipy.ndimage import median_filter


class WireAnalyzer:
    """Wire diameter measurement using edge analysis"""

    # ── preprocessing ──────────────────────────────────────────────────

    def preprocess(self, image: np.ndarray) -> np.ndarray:
        gray = cv2.cvtColor(image, cv2.COLOR_BGR2GRAY)
        # Увеличиваем размытие — подавляем шум на поверхности провода
        blur = cv2.GaussianBlur(gray, (9, 9), 2)
        return blur
    
    def detect_edges(self, blur: np.ndarray) -> np.ndarray:
        edges = cv2.Canny(blur, 30, 100)

        # Убираем мелкие разрывы по горизонтали — соединяем близкие точки
        kernel_close = cv2.getStructuringElement(cv2.MORPH_RECT, (15, 1))
        edges = cv2.morphologyEx(edges, cv2.MORPH_CLOSE, kernel_close)

        # Убираем одиночные пиксели и мелкий шум
        kernel_open = cv2.getStructuringElement(cv2.MORPH_RECT, (3, 1))
        edges = cv2.morphologyEx(edges, cv2.MORPH_OPEN, kernel_open)

        return edges

    # ── edge extraction ─────────────────────────────────────────────────

    def extract_edges(self, edges: np.ndarray):
        xs, top_y, bottom_y = [], [], []

        for x in range(edges.shape[1]):
            ys = np.where(edges[:, x] > 0)[0]
            if len(ys) > 1:
                xs.append(x)
                top_y.append(ys[0])
                bottom_y.append(ys[-1])

        if len(xs) == 0:
            return np.array(xs), np.array(top_y), np.array(bottom_y)

        xs     = np.array(xs)
        top_y  = np.array(top_y,    dtype=float)
        bottom_y = np.array(bottom_y, dtype=float)

        # Сглаживаем сами границы — убираем выбросы
        top_y    = self._smooth_edges(top_y)
        bottom_y = self._smooth_edges(bottom_y)

        return xs, top_y.astype(int), bottom_y.astype(int)

    # ── diameter math ───────────────────────────────────────────────────

    def compute_diameter_px(self, top_y: np.ndarray, bottom_y: np.ndarray) -> np.ndarray:
        """
        Диаметр по нормали к центральной линии — точнее вертикального.
        """
        center_y = (top_y + bottom_y) / 2.0
        center_smooth = self._smooth(center_y)

        d_dx = np.gradient(center_smooth)
        normal_factor = 1.0 / np.sqrt(1.0 + d_dx ** 2)

        return (bottom_y - top_y) * normal_factor

    def _smooth(self, signal: np.ndarray, kernel_size: int = 21) -> np.ndarray:
        kernel = np.ones(kernel_size) / kernel_size
        return np.convolve(signal, kernel, mode='same')

    def _smooth_edges(self, signal: np.ndarray, kernel_size: int = 15) -> np.ndarray:
        """Медианный фильтр + скользящее среднее для сглаживания границ"""
        signal = median_filter(signal, size=kernel_size)
        signal = self._smooth(signal, kernel_size)
        return signal

    def _robust_filter(self, diameters: np.ndarray, k: float = 2.0) -> np.ndarray:
        """Убирает выбросы через MAD."""
        median = np.median(diameters)
        mad = np.median(np.abs(diameters - median))

        if mad == 0:
            return diameters

        return diameters[(diameters >= median - k * mad) & (diameters <= median + k * mad)]

    # ── public API ──────────────────────────────────────────────────────

    # def measure_diameter_at_x(self, image: np.ndarray, x_coord: int):
    #     """
    #     Измеряет диаметр в одном столбце x_coord.
    #     Используется при клике пользователя для калибровки.

    #     Returns:
    #         (diameter_px, top_y, bottom_y)
    #     """
    #     edges = self.detect_edges(self.preprocess(image))

    #     ys = np.where(edges[:, x_coord] > 0)[0]

    #     if len(ys) < 2:
    #         raise RuntimeError(f"Wire edges not found at x={x_coord}")

    #     top_y = int(ys[0])
    #     bottom_y = int(ys[-1])

    #     return bottom_y - top_y, top_y, bottom_y
    def measure_diameter_at_x(self, image: np.ndarray, x_coord: int, window: int = 20):
        edges = self.detect_edges(self.preprocess(image))
        
        # Используем сглаженные границы вместо сырых edges
        xs_all, tops_all, bots_all = self.extract_edges(edges)
        
        if len(xs_all) == 0:
            raise RuntimeError(f"Wire not detected")

        # Фильтруем только окно вокруг x_coord
        mask = (xs_all >= x_coord - window) & (xs_all <= x_coord + window)
        xs   = xs_all[mask].astype(float)
        tops = tops_all[mask].astype(float)
        bots = bots_all[mask].astype(float)

        if len(xs) < 3:
            raise RuntimeError(f"Wire edges not found near x={x_coord}")

        # Наклон центральной линии через линейную регрессию
        center = (tops + bots) / 2.0
        slope  = np.polyfit(xs, center, 1)[0]

        normal_factor = 1.0 / np.sqrt(1.0 + slope ** 2)

        # Диаметр в точке клика
        idx = np.argmin(np.abs(xs - x_coord))
        diameter_px = float((bots[idx] - tops[idx]) * normal_factor)

        return diameter_px, int(tops[idx]), int(bots[idx]), slope
    
    def measure(self, image: np.ndarray):
        """
        Измеряет средний диаметр по всему изображению.
        Используется после калибровки для замера в мм.

        Returns:
            (mean_diameter_px, filtered_diameters)
        """
        edges = self.detect_edges(self.preprocess(image))
        xs, top_y, bottom_y = self.extract_edges(edges)

        if len(xs) < 10:
            raise RuntimeError("Wire not detected — not enough edge points")

        diameters = self.compute_diameter_px(top_y, bottom_y)
        filtered = self._robust_filter(diameters)

        return float(np.mean(filtered)), filtered
    
    def get_edge_points(self, image: np.ndarray):
        """
        Возвращает все найденные края проволоки по всей картинке.
        Returns: (xs, top_y, bottom_y)
        """
        edges = self.detect_edges(self.preprocess(image))
        return self.extract_edges(edges)