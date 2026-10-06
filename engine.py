import numpy as np
import networkx as nx
from typing import Dict, Any

from terrain import TerrainAnalyzer
from generation import (
    seed_anchors,
    grow_arterial_network,
    subdivide_secondary,
    extract_blocks,
    place_buildings
)
from philosophy import PHILOSOPHIES

class CityGenerator:
    def __init__(self, height_map: np.ndarray, philosophy_name: str, slope_tolerance: float, scale: float = 1.0):
        self.height_map = height_map
        if philosophy_name not in PHILOSOPHIES:
            raise ValueError(f"Unknown philosophy: {philosophy_name}")
        self.philosophy = PHILOSOPHIES[philosophy_name]
        self.slope_tolerance = slope_tolerance
        self.scale = scale

        # Generation outputs
        self.terrain_analyzer = None
        self.anchors = []
        self.primary_network = None
        self.full_network = None
        self.blocks = []
        self.buildings = []

    def generate(self) -> Dict[str, Any]:
        """
        Executes the 6-phase algorithmic pipeline.
        """
        bounds = self.height_map.shape

        # PHASE 1: TERRAIN ANALYSIS
        print("Phase 1: Terrain Analysis...")
        self.terrain_analyzer = TerrainAnalyzer(self.height_map, self.slope_tolerance)
        self.terrain_analyzer.compute_gradient_field()
        cost_field = self.terrain_analyzer.generate_cost_field(self.philosophy.max_slope.value)

        # PHASE 2: CIVIC ANCHOR SEEDING
        print("Phase 2: Civic Anchor Seeding...")
        self.anchors = seed_anchors(self.height_map, cost_field, self.philosophy)

        # PHASE 3: PRIMARY ARTERIAL NETWORK
        print("Phase 3: Primary Arterial Network...")
        self.primary_network = grow_arterial_network(self.anchors, self.height_map, cost_field, self.philosophy)

        # PHASE 4: SECONDARY AND LOCAL INFILL
        print("Phase 4: Secondary and Local Infill...")
        self.full_network = subdivide_secondary(self.primary_network, self.philosophy, bounds)

        # PHASE 5: BLOCK AND PARCEL SUBDIVISION
        print("Phase 5: Block and Parcel Subdivision...")
        self.blocks = extract_blocks(self.full_network, bounds)

        # PHASE 6: BUILDING FOOTPRINT AND CIVIC PLACEMENT
        print("Phase 6: Building Placement...")
        self.buildings = place_buildings(self.blocks, self.philosophy)

        print("Generation Complete.")

        return {
            "anchors": self.anchors,
            "primary_network": self.primary_network,
            "full_network": self.full_network,
            "blocks": self.blocks,
            "buildings": self.buildings,
            "cost_field": cost_field,
            "zones": self.terrain_analyzer.get_geological_zones()
        }
