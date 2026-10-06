import networkx as nx
import numpy as np
from typing import Tuple, List, Dict, Any
from shapely.geometry import Polygon, Point, LineString
import math

def seed_anchors(height_map: np.ndarray, cost_field: np.ndarray, philosophy_config: Any) -> List[Tuple[int, int]]:
    """
    PHASE 2: CIVIC ANCHOR SEEDING
    Determine primary nodes based on the philosophy.
    Returns a list of anchor coordinates (y, x).
    """
    h, w = height_map.shape
    anchors = []

    # Mock implementations for a few anchor types based on philosophy
    # In a full implementation, this would match to the philosophy's specific rules

    if "Plaza" in philosophy_config.name or "Castrum" in philosophy_config.name or "Grid" in philosophy_config.name:
        # Central geographic nodes
        center_y, center_x = h // 2, w // 2
        anchors.append((center_y, center_x))

    elif "Star Fort" in philosophy_config.name or "Baroque" in philosophy_config.name:
        # Center of the map for radial layout
        center_y, center_x = h // 2, w // 2
        anchors.append((center_y, center_x))

    elif "Organic" in philosophy_config.name or "Topographic" in philosophy_config.name:
        # Defensive high ground (highest point in the map)
        max_idx = np.argmax(height_map)
        max_y, max_x = np.unravel_index(max_idx, height_map.shape)
        anchors.append((max_y, max_x))

    elif "Coast" in philosophy_config.name or "Terraced" in philosophy_config.name:
        # Shorefronts (find edge of water)
        # Assuming water is height == 0
        water_mask = height_map <= 0.05
        # Find a point near the water edge
        # Mock logic
        anchors.append((h // 2, w // 4))

    else:
        # Default fallback
        anchors.append((h // 2, w // 2))

    return anchors

def grow_arterial_network(anchors: List[Tuple[int, int]], height_map: np.ndarray, cost_field: np.ndarray, philosophy_config: Any) -> nx.Graph:
    """
    PHASE 3: PRIMARY ARTERIAL NETWORK
    Grow primary graph edges connecting anchor nodes or projecting across the map.
    """
    G = nx.Graph()
    h, w = height_map.shape

    for idx, anchor in enumerate(anchors):
        G.add_node(idx, pos=(anchor[1], anchor[0]), type='anchor')

    network_type = philosophy_config.network_type.name

    # Simple mock implementations for different network topologies

    if "GRID" in network_type or "AXES" in network_type or "ORTHOGONAL" in network_type:
        # Cast straight rays along defined coordinate axes
        center = anchors[0]
        # Cardinal directions
        directions = [(0, 1), (1, 0), (0, -1), (-1, 0)]
        step_size = max(10, min(w, h) // 5)

        node_idx = len(anchors)
        for dy, dx in directions:
            cy, cx = center
            prev_node = 0
            for i in range(1, 4):
                ny, nx_ = cy + dy * step_size * i, cx + dx * step_size * i
                if 0 <= ny < h and 0 <= nx_ < w:
                    G.add_node(node_idx, pos=(nx_, ny), type='arterial')
                    G.add_edge(prev_node, node_idx)
                    prev_node = node_idx
                    node_idx += 1
                else:
                    break

    elif "RADIAL" in network_type or "RAYS" in network_type:
        # Project rays outward from central anchors
        center = anchors[0]
        num_rays = 8
        step_size = max(10, min(w, h) // 4)

        node_idx = len(anchors)
        for i in range(num_rays):
            angle = 2 * math.pi * i / num_rays
            dy, dx = math.sin(angle), math.cos(angle)
            cy, cx = center

            prev_node = 0
            for j in range(1, 3):
                ny, nx_ = int(cy + dy * step_size * j), int(cx + dx * step_size * j)
                if 0 <= ny < h and 0 <= nx_ < w:
                    G.add_node(node_idx, pos=(nx_, ny), type='arterial')
                    G.add_edge(prev_node, node_idx)
                    prev_node = node_idx
                    node_idx += 1
                else:
                    break

    elif "CONTOURS" in network_type or "RIBBONS" in network_type or "CURVILINEAR" in network_type or "PODS" in network_type:
        # Organic, follows contours
        # Mocking by creating a random curved path or just a simple branching
        center = anchors[0]
        node_idx = len(anchors)

        # 3 branching paths
        for i in range(3):
            angle = 2 * math.pi * i / 3
            cy, cx = center
            prev_node = 0
            for j in range(1, 4):
                # Add some curve
                angle += np.random.uniform(-0.5, 0.5)
                dy, dx = math.sin(angle), math.cos(angle)
                ny, nx_ = int(cy + dy * 20), int(cx + dx * 20)

                if 0 <= ny < h and 0 <= nx_ < w:
                    G.add_node(node_idx, pos=(nx_, ny), type='arterial')
                    G.add_edge(prev_node, node_idx)
                    prev_node = node_idx
                    node_idx += 1
                    cy, cx = ny, nx_
                else:
                    break

    elif "LINEAR" in network_type:
        # Dominant, straight central spine
        center = anchors[0]
        node_idx = len(anchors)

        cy, cx = center
        prev_node = 0
        # Go right
        for i in range(1, 5):
            ny, nx_ = cy, cx + 20 * i
            if 0 <= ny < h and 0 <= nx_ < w:
                G.add_node(node_idx, pos=(nx_, ny), type='arterial')
                G.add_edge(prev_node, node_idx)
                prev_node = node_idx
                node_idx += 1

        prev_node = 0
        # Go left
        for i in range(1, 5):
            ny, nx_ = cy, cx - 20 * i
            if 0 <= ny < h and 0 <= nx_ < w:
                G.add_node(node_idx, pos=(nx_, ny), type='arterial')
                G.add_edge(prev_node, node_idx)
                prev_node = node_idx
                node_idx += 1

    else:
        # Default grid-ish
        center = anchors[0]
        node_idx = len(anchors)
        for dy, dx in [(0, 1), (1, 0), (0, -1), (-1, 0)]:
            ny, nx_ = center[0] + dy * 30, center[1] + dx * 30
            if 0 <= ny < h and 0 <= nx_ < w:
                G.add_node(node_idx, pos=(nx_, ny), type='arterial')
                G.add_edge(0, node_idx)
                node_idx += 1

    return G

def subdivide_secondary(G_primary: nx.Graph, philosophy_config: Any, bounds: Tuple[int, int]) -> nx.Graph:
    """
    PHASE 4: SECONDARY AND LOCAL INFILL
    Subdivide areas between primary arterials into local access roads.
    """
    G = G_primary.copy()
    node_idx = max(G.nodes) + 1

    # Extract nodes
    nodes = list(G_primary.nodes(data=True))

    # Mocking: just add some perpendicular short roads to existing arterials
    edges = list(G_primary.edges())

    # Only add to a subset to keep it simple
    for u, v in edges[:10]:
        pos_u = G.nodes[u]['pos']
        pos_v = G.nodes[v]['pos']

        # Midpoint
        mx, my = (pos_u[0] + pos_v[0]) / 2, (pos_u[1] + pos_v[1]) / 2

        # Perpendicular vector
        dx, dy = pos_v[0] - pos_u[0], pos_v[1] - pos_u[1]
        length = math.sqrt(dx**2 + dy**2)
        if length == 0:
            continue

        pdx, pdy = -dy/length * 15, dx/length * 15

        nx1, ny1 = int(mx + pdx), int(my + pdy)
        nx2, ny2 = int(mx - pdx), int(my - pdy)

        if 0 <= nx1 < bounds[1] and 0 <= ny1 < bounds[0]:
            G.add_node(node_idx, pos=(nx1, ny1), type='secondary')
            # Add node at midpoint
            G.add_node(node_idx+1, pos=(int(mx), int(my)), type='arterial')
            # Remove old edge and add new ones
            G.remove_edge(u, v)
            G.add_edge(u, node_idx+1)
            G.add_edge(node_idx+1, v)

            G.add_edge(node_idx+1, node_idx)
            node_idx += 2

    return G

def extract_blocks(G: nx.Graph, bounds: Tuple[int, int]) -> List[Polygon]:
    """
    PHASE 5: BLOCK AND PARCEL SUBDIVISION
    Extract closed polygons bounded by the road network.
    """
    # In a full implementation, we'd use a graph planarization and face extraction algorithm
    # like finding cycles in the graph.
    # For mocking, we'll just create some squares around the nodes.

    blocks = []

    for node, data in G.nodes(data=True):
        if data.get('type') == 'anchor':
            continue

        pos = data['pos']
        # Create a small square block near the node
        size = 10
        x, y = pos[0], pos[1]

        # Offset slightly to be a block adjacent to the road
        polygon = Polygon([
            (x + 2, y + 2),
            (x + size, y + 2),
            (x + size, y + size),
            (x + 2, y + size)
        ])

        if polygon.is_valid:
            blocks.append(polygon)

    return blocks

def place_buildings(blocks: List[Polygon], philosophy_config: Any) -> List[Polygon]:
    """
    PHASE 6: BUILDING FOOTPRINT AND CIVIC PLACEMENT
    Extrude building footprints onto parcels.
    """
    buildings = []

    for block in blocks:
        # Shrink the block to create a setback
        try:
            building = block.buffer(-1.0) # 1 unit setback
            if not building.is_empty and isinstance(building, Polygon):
                buildings.append(building)
        except Exception:
            pass

    return buildings
