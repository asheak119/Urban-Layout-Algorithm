import numpy as np
from PIL import Image
import scipy.ndimage as ndimage

class TerrainProcessor:
    def __init__(self, image_pil):
        # Convert to grayscale
        self.image = image_pil.convert('L')
        # Normalize to 0.0 - 1.0
        self.elevation = np.array(self.image, dtype=np.float32) / 255.0
        self.height, self.width = self.elevation.shape
        self.water_mask = None
        self.gradient_mag = None
        self.gradient_dir = None

    def calculate_water_mask(self, threshold=0.1):
        """Creates a boolean mask where True indicates water."""
        self.water_mask = self.elevation <= threshold
        return self.water_mask

    def calculate_gradients(self):
        """Calculates the slope magnitude and direction."""
        # Using Sobel filters to calculate gradient
        dy = ndimage.sobel(self.elevation, axis=0)
        dx = ndimage.sobel(self.elevation, axis=1)

        # Magnitude of gradient (slope)
        self.gradient_mag = np.hypot(dx, dy)

        # Direction of gradient
        self.gradient_dir = np.arctan2(dy, dx)

        return self.gradient_mag, self.gradient_dir

    def get_buildable_mask(self, max_slope, water_threshold=0.1):
        """Returns a boolean mask where True indicates buildable land."""
        if self.water_mask is None:
            self.calculate_water_mask(water_threshold)
        if self.gradient_mag is None:
            self.calculate_gradients()

        buildable = (~self.water_mask) & (self.gradient_mag <= max_slope)
        return buildable
