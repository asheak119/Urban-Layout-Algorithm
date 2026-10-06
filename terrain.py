import numpy as np
from scipy import ndimage
import matplotlib.pyplot as plt
from PIL import Image

class TerrainAnalyzer:
    def __init__(self, height_map: np.ndarray, slope_tolerance: float):
        self.height_map = height_map
        self.slope_tolerance = slope_tolerance
        self.gradient_magnitude = None
        self.gradient_direction = None
        self.cost_field = None

    def compute_gradient_field(self):
        """Computes gradient field (slope magnitude and aspect direction)"""
        # Sobel operator for gradients
        dx = ndimage.sobel(self.height_map, axis=1)
        dy = ndimage.sobel(self.height_map, axis=0)

        # Calculate magnitude and direction
        self.gradient_magnitude = np.hypot(dx, dy)
        self.gradient_direction = np.arctan2(dy, dx)

        return self.gradient_magnitude, self.gradient_direction

    def calculate_contour_lines(self, levels=10):
        """Generates contour lines (iso-elevation paths)"""
        # In a full implementation, this might return geometry paths.
        # For our mock implementation, we return a contour plot setup.
        fig, ax = plt.subplots()
        contour = ax.contour(self.height_map, levels=levels)
        plt.close(fig)
        return contour

    def generate_cost_field(self, max_slope_val: float):
        """Generates cost field based on slope, water proximity, and philosophy max_slope_val"""
        if self.gradient_magnitude is None:
            self.compute_gradient_field()

        # Slider scales the engine's internal gradient thresholds uniformly
        cliff_threshold = self.slope_tolerance

        # Normalize the gradient by the cliff threshold
        normalized_slope = self.gradient_magnitude / cliff_threshold

        # Cost is non-linear based on slope
        self.cost_field = np.zeros_like(self.height_map, dtype=float)

        # Flat Ground: 0 to 20 percent of the Cliff Threshold
        flat_mask = normalized_slope <= 0.20
        self.cost_field[flat_mask] = 1.0

        # Gentle Slope: 20 to 45 percent of the Cliff Threshold
        gentle_mask = (normalized_slope > 0.20) & (normalized_slope <= 0.45)
        self.cost_field[gentle_mask] = 2.0

        # Moderate Slope: 45 to 70 percent of the Cliff Threshold
        moderate_mask = (normalized_slope > 0.45) & (normalized_slope <= 0.70)
        self.cost_field[moderate_mask] = 5.0

        # Steep Slope: 70 to 100 percent of the Cliff Threshold
        steep_mask = (normalized_slope > 0.70) & (normalized_slope <= 1.0)
        self.cost_field[steep_mask] = 10.0

        # Cliff: Greater than 100 percent of the Cliff Threshold
        cliff_mask = normalized_slope > 1.0
        self.cost_field[cliff_mask] = 100.0 # High cost for cliff

        # Check against philosophy max slope
        invalid_mask = normalized_slope > max_slope_val
        self.cost_field[invalid_mask] = 1000.0 # Impassable if exceeds philosophy slope

        return self.cost_field

    def check_line_cost(self, p1, p2):
        """
        Calculates the maximum cost along a straight line between p1(y1, x1) and p2(y2, x2).
        Returns the max cost. If it exceeds 100, the path is generally impassable.
        """
        if self.cost_field is None:
            return 1000.0

        y1, x1 = p1
        y2, x2 = p2

        # Number of points to sample
        dist = np.hypot(y2 - y1, x2 - x1)
        if dist == 0:
            return self.cost_field[int(y1), int(x1)]

        num_points = int(np.ceil(dist))

        y_pts = np.linspace(y1, y2, num_points)
        x_pts = np.linspace(x1, x2, num_points)

        max_cost = 0.0
        h, w = self.cost_field.shape

        for y, x in zip(y_pts, x_pts):
            iy, ix = int(np.round(y)), int(np.round(x))
            if 0 <= iy < h and 0 <= ix < w:
                cost = self.cost_field[iy, ix]
                if cost > max_cost:
                    max_cost = cost
            else:
                return 1000.0 # Out of bounds

        return max_cost

    def get_geological_zones(self):
        """Map distinct geological zones"""
        if self.gradient_magnitude is None:
            self.compute_gradient_field()

        normalized_slope = self.gradient_magnitude / self.slope_tolerance

        zones = np.zeros_like(self.height_map, dtype=int)
        zones[normalized_slope <= 0.20] = 0 # Flat plains
        zones[(normalized_slope > 0.20) & (normalized_slope <= 0.45)] = 1 # Rolling terrain
        zones[(normalized_slope > 0.45) & (normalized_slope <= 1.0)] = 2 # Steep terrain
        zones[normalized_slope > 1.0] = 3 # Cliffs
        # Water bodies would be another zone based on absolute height, e.g. height == 0
        zones[self.height_map <= 0.05] = 4 # Water

        return zones
