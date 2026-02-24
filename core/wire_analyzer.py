import cv2
import numpy as np


class WireAnalyzer:
    """Wire diameter measurement using edge analysis"""

    # ── preprocessing ──────────────────────────────────────────────────

    def preprocess(self, image: np.ndarray) -> np.ndarray:
        gray = cv2.cvtColor(image, cv2.COLOR_BGR2GRAY)
        return cv2.GaussianBlur(gray, (5, 5), 0)

    def detect_edges(self, blur: np.ndarray) -> np.ndarray:
        return cv2.Canny(blur, 50, 150)

    # ── edge extraction ─────────────────────────────────────────────────

    def extract_edges(self, edges: np.ndarray):
        """
        Для каждого столбца находит верхний и нижний край проволоки.
        Возвращает (xs, top_y, bottom_y) — numpy arrays.
        """
        xs, top_y, bottom_y = [], [], []

        for x in range(edges.shape[1]):
            ys = np.where(edges[:, x] > 0)[0]
            if len(ys) > 1:
                xs.append(x)
                top_y.append(ys[0])
                bottom_y.append(ys[-1])

        return np.array(xs), np.array(top_y), np.array(bottom_y)

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

    def _robust_filter(self, diameters: np.ndarray, k: float = 2.0) -> np.ndarray:
        """Убирает выбросы через MAD."""
        median = np.median(diameters)
        mad = np.median(np.abs(diameters - median))

        if mad == 0:
            return diameters

        return diameters[(diameters >= median - k * mad) & (diameters <= median + k * mad)]

    # ── public API ──────────────────────────────────────────────────────

    def measure_diameter_at_x(self, image: np.ndarray, x_coord: int):
        """
        Измеряет диаметр в одном столбце x_coord.
        Используется при клике пользователя для калибровки.

        Returns:
            (diameter_px, top_y, bottom_y)
        """
        edges = self.detect_edges(self.preprocess(image))

        ys = np.where(edges[:, x_coord] > 0)[0]

        if len(ys) < 2:
            raise RuntimeError(f"Wire edges not found at x={x_coord}")

        top_y = int(ys[0])
        bottom_y = int(ys[-1])

        return bottom_y - top_y, top_y, bottom_y

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