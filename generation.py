import networkx as nx
import numpy as np
from typing import Tuple, List, Dict, Any
from shapely.geometry import Polygon, Point, LineString
from shapely.ops import polygonize, split
import math
from collections import deque

def seed_anchors(height_map: np.ndarray, cost_field: np.ndarray, philosophy_config: Any) -> List[Tuple[int, int]]:
    """
    PHASE 2: CIVIC ANCHOR SEEDING
    Determine primary nodes based on the philosophy.
    Returns a list of anchor coordinates (y, x).
    """
    h, w = height_map.shape
    anchors = []

    # Simple central node for most
    if "Plaza" in philosophy_config.name or "Castrum" in philosophy_config.name or "Grid" in philosophy_config.name:
        anchors.append((h // 2, w // 2))
    elif "Organic" in philosophy_config.name or "Topographic" in philosophy_config.name:
        max_idx = np.argmax(height_map)
        max_y, max_x = np.unravel_index(max_idx, height_map.shape)
        anchors.append((max_y, max_x))
    else:
        anchors.append((h // 2, w // 2))

    return anchors

def check_line_cost(cost_field: np.ndarray, p1: Tuple[float, float], p2: Tuple[float, float]) -> float:
    """Calculates average cost along a line for iterative path testing."""
    if cost_field is None:
        return 1000.0
    y1, x1 = p1
    y2, x2 = p2
    dist = np.hypot(y2 - y1, x2 - x1)
    if dist == 0:
        return cost_field[int(y1), int(x1)]
    num_points = int(np.ceil(dist))
    y_pts = np.linspace(y1, y2, num_points)
    x_pts = np.linspace(x1, x2, num_points)

    total_cost = 0.0
    valid_points = 0
    h, w = cost_field.shape

    for y, x in zip(y_pts, x_pts):
        iy, ix = int(np.round(y)), int(np.round(x))
        if 0 <= iy < h and 0 <= ix < w:
            cost = cost_field[iy, ix]
            if cost >= 100.0: # Impassable
                return 1000.0
            total_cost += cost
            valid_points += 1
        else:
            return 1000.0

    if valid_points == 0:
        return 1000.0
    return total_cost / valid_points

def get_best_path(cy: float, cx: float, base_angle: float, step_size: float, cost_field: np.ndarray, bounds: Tuple[int, int]) -> Tuple[float, float, float]:
    """
    Iterative terrain testing.
    Samples multiple angles around the base_angle and picks the one with the lowest cost.
    Returns (ny, nx, best_angle). Returns None if all are impassable.
    """
    h, w = bounds
    best_cost = 1000.0
    best_pos = None
    best_angle = None

    # Sample -30 to 30 degrees around base angle
    angles_to_test = [base_angle] + [base_angle + math.radians(d) for d in range(-30, 31, 10) if d != 0]

    for test_angle in angles_to_test:
        ny = cy + step_size * math.sin(test_angle)
        nx_ = cx + step_size * math.cos(test_angle)

        if not (0 <= ny < h and 0 <= nx_ < w):
            continue

        cost = check_line_cost(cost_field, (cy, cx), (ny, nx_))
        if cost < best_cost:
            best_cost = cost
            best_pos = (ny, nx_)
            best_angle = test_angle

    if best_cost >= 100.0:
        return None

    return best_pos[0], best_pos[1], best_angle

def _run_agents(G, start_nodes, bounds, cost_field, network_type, step_size, max_nodes=500):
    """Internal agent-based network generator."""
    h, w = bounds
    # queue contains: (current_node_id, (y, x), angle, depth, type)
    queue = deque()

    for u, data in start_nodes.items():
        y, x = data['pos'][1], data['pos'][0]
        if "RADIAL" in network_type or "RAYS" in network_type or "CONCENTRIC" in network_type:
            num_rays = 8
            for i in range(num_rays):
                angle = 2 * math.pi * i / num_rays
                queue.append((u, (y, x), angle, 0, 'arterial'))
        else:
            for angle in [0, math.pi/2, math.pi, 3*math.pi/2]:
                queue.append((u, (y, x), angle, 0, 'arterial'))

    node_idx = max(G.nodes) + 1 if G.nodes else 0

    while queue and len(G.nodes) < max_nodes:
        parent_id, (cy, cx), angle, depth, rtype = queue.popleft()

        # Iteratively test terrain for the best path forward
        result = get_best_path(cy, cx, angle, step_size, cost_field, bounds)
        if result is None:
            continue # Terrain too steep or out of bounds

        ny, nx_, chosen_angle = result

        # Check proximity to existing nodes to snap (create loops)
        snapped = False
        for n, data in G.nodes(data=True):
            if n == parent_id:
                continue
            ey, ex = data['pos'][1], data['pos'][0]
            if np.hypot(ny - ey, nx_ - ex) < step_size * 0.7:
                # Snap to this node
                if not G.has_edge(parent_id, n):
                    G.add_edge(parent_id, n)
                snapped = True
                break

        if snapped:
            continue

        # Add new node and edge
        current_id = node_idx
        G.add_node(current_id, pos=(nx_, ny), type=rtype)
        G.add_edge(parent_id, current_id)
        node_idx += 1

        # Branching logic
        if "GRID" in network_type or "AXES" in network_type or "ORTHOGONAL" in network_type:
            queue.append((current_id, (ny, nx_), chosen_angle, depth+1, rtype))
            if depth % 2 == 0:
                queue.append((current_id, (ny, nx_), chosen_angle + math.pi/2, depth+1, rtype))
                queue.append((current_id, (ny, nx_), chosen_angle - math.pi/2, depth+1, rtype))

        elif "RADIAL" in network_type or "RAYS" in network_type or "CONCENTRIC" in network_type:
            queue.append((current_id, (ny, nx_), chosen_angle, depth+1, rtype))
            if depth % 3 == 0:
                queue.append((current_id, (ny, nx_), chosen_angle + math.pi/4, depth+1, rtype))
                queue.append((current_id, (ny, nx_), chosen_angle - math.pi/4, depth+1, rtype))

        elif "CONTOURS" in network_type or "CURVILINEAR" in network_type or "PODS" in network_type:
            noise = np.random.uniform(-0.3, 0.3)
            queue.append((current_id, (ny, nx_), chosen_angle + noise, depth+1, rtype))
            if np.random.random() < 0.3:
                queue.append((current_id, (ny, nx_), chosen_angle + math.pi/2 + noise, depth+1, rtype))
            if np.random.random() < 0.3:
                queue.append((current_id, (ny, nx_), chosen_angle - math.pi/2 + noise, depth+1, rtype))
        else:
            queue.append((current_id, (ny, nx_), chosen_angle, depth+1, rtype))
            if np.random.random() < 0.5:
                queue.append((current_id, (ny, nx_), chosen_angle + math.pi/2, depth+1, rtype))

    return G

def grow_arterial_network(anchors: List[Tuple[int, int]], height_map: np.ndarray, cost_field: np.ndarray, philosophy_config: Any) -> nx.Graph:
    """
    PHASE 3: PRIMARY ARTERIAL NETWORK
    """
    G = nx.Graph()
    h, w = height_map.shape
    start_nodes = {}

    for idx, anchor in enumerate(anchors):
        G.add_node(idx, pos=(anchor[1], anchor[0]), type='anchor')
        start_nodes[idx] = {'pos': (anchor[1], anchor[0])}

    network_type = philosophy_config.network_type.name
    step_size = max(10, min(w, h) // 10)

    G = _run_agents(G, start_nodes, (h, w), cost_field, network_type, step_size, max_nodes=300)
    return G

def subdivide_secondary(G_primary: nx.Graph, philosophy_config: Any, bounds: Tuple[int, int], cost_field: np.ndarray) -> nx.Graph:
    """
    PHASE 4: SECONDARY AND LOCAL INFILL
    """
    G = G_primary.copy()
    h, w = bounds
    network_type = philosophy_config.network_type.name
    step_size = max(5, min(w, h) // 20)

    start_nodes = {}
    for n, data in list(G.nodes(data=True)):
        if data.get('type') == 'arterial' and np.random.random() < 0.5:
            start_nodes[n] = data

    G = _run_agents(G, start_nodes, bounds, cost_field, network_type, step_size, max_nodes=len(G.nodes)+600)
    return G

def get_longest_axis(poly: Polygon) -> LineString:
    """Finds a line along the longest axis of the minimum rotated rectangle."""
    mrr = poly.minimum_rotated_rectangle
    coords = list(mrr.exterior.coords)
    # The edges are (coords[0], coords[1]) and (coords[1], coords[2])
    dist1 = Point(coords[0]).distance(Point(coords[1]))
    dist2 = Point(coords[1]).distance(Point(coords[2]))

    if dist1 > dist2:
        # Longest axis is parallel to coords[0]->coords[1], passing through center
        p1, p2 = coords[0], coords[1]
    else:
        p1, p2 = coords[1], coords[2]

    # Vector
    dx = p2[0] - p1[0]
    dy = p2[1] - p1[1]

    # Center of poly
    cx, cy = poly.centroid.x, poly.centroid.y

    # Create a line going through center perpendicular to longest axis?
    # Or parallel to shorter axis to cut it?
    # To bisect a long block into two squarish lots, we cut across the long axis.
    # So we want a line parallel to the *shorter* edge.

    if dist1 > dist2:
        p1_s, p2_s = coords[1], coords[2] # shorter edge
    else:
        p1_s, p2_s = coords[0], coords[1]

    dx_s = p2_s[0] - p1_s[0]
    dy_s = p2_s[1] - p1_s[1]

    # Make a long line through the center
    L = 1000
    # Normalize
    length = math.hypot(dx_s, dy_s)
    if length == 0:
        return LineString([(cx, cy - L), (cx, cy + L)])

    dx_s, dy_s = dx_s / length, dy_s / length

    return LineString([(cx - dx_s * L, cy - dy_s * L), (cx + dx_s * L, cy + dy_s * L)])


def extract_blocks(G: nx.Graph, bounds: Tuple[int, int]) -> List[Polygon]:
    """
    PHASE 5: BLOCK AND PARCEL SUBDIVISION
    Use shapely polygonize on the road network to extract blocks.
    """
    lines = []
    for u, v in G.edges():
        p1 = G.nodes[u]['pos']
        p2 = G.nodes[v]['pos']
        lines.append(LineString([p1, p2]))

    polygons = list(polygonize(lines))

    subdivided_blocks = []

    def subdivide(poly, depth):
        if depth == 0 or poly.area < 50:
            if poly.area > 10:
                subdivided_blocks.append(poly)
            return

        try:
            splitter = get_longest_axis(poly)
            result = split(poly, splitter)
            if len(result.geoms) > 1:
                for geom in result.geoms:
                    subdivide(geom, depth - 1)
            else:
                if poly.area > 10:
                    subdivided_blocks.append(poly)
        except Exception:
            if poly.area > 10:
                subdivided_blocks.append(poly)

    for poly in polygons:
        subdivide(poly, 2) # max 2 recursive splits

    return subdivided_blocks

def place_buildings(blocks: List[Polygon], philosophy_config: Any) -> List[Dict[str, Any]]:
    """
    PHASE 6: BUILDING FOOTPRINT AND CIVIC PLACEMENT
    Map lots to building types.
    """
    buildings = []

    for block in blocks:
        try:
            # Setback
            footprint = block.buffer(-1.0)
            if footprint.is_empty or not isinstance(footprint, Polygon):
                continue

            # Assign type based on area
            area = footprint.area
            if area > 100:
                btype = 'civic'
                color = 'purple'
            elif area > 50:
                btype = 'commercial'
                color = 'blue'
            else:
                btype = 'residential'
                color = 'orange'

            buildings.append({
                'polygon': footprint,
                'type': btype,
                'color': color
            })
        except Exception:
            pass

    return buildings
