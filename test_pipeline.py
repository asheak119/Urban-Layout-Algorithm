from PIL import Image
from app import load_philosophies
from terrain import TerrainProcessor
from layout import LayoutEngine
from render import render_layout_plotly
import sys
import configparser

def load_philosophies_safe(filepath="philosophies_config.txt"):
    config = configparser.RawConfigParser()
    config.read(filepath)
    philosophies = {}
    for section in config.sections():
        phil_id = config.get(section, 'id', fallback=section)
        philosophies[phil_id] = {
            'name': config.get(section, 'name', fallback=phil_id),
            'topology': config.get(section, 'topology', fallback=''),
            'block_pattern': config.get(section, 'block_pattern', fallback=''),
            'anchors': config.get(section, 'anchors', fallback=''),
            'density': config.get(section, 'density', fallback=''),
            'slope_tolerance': config.get(section, 'slope_tolerance', fallback=''),
            'terrain_behavior': config.get(section, 'terrain_behavior', fallback='')
        }
    return philosophies

def main():
    print("Loading image...")
    image = Image.open('/tmp/file_attachments/IMG_4828.jpeg')

    print("Loading configurations...")
    philosophies = load_philosophies_safe()
    config = philosophies['roman_castrum']

    print("Processing terrain...")
    tp = TerrainProcessor(image)
    tp.calculate_water_mask(threshold=0.1)
    tp.calculate_gradients()

    print("Generating layout...")
    le = LayoutEngine(tp, config, scale=10.0, slope_tolerance=0.5)
    success = le.generate()

    if success:
        print("Rendering layout...")
        fig = render_layout_plotly(tp, le)
        fig.write_image('test_output.png')
        print("Saved to test_output.png")
    else:
        print("Failed to generate layout.")
        sys.exit(1)

if __name__ == "__main__":
    main()
