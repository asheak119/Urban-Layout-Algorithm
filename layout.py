import networkx as nx
import numpy as np
from shapely.geometry import Point, LineString, Polygon
from shapely.ops import polygonize
import math
import random

class LayoutEngine:
    def __init__(self, terrain, philosophy_config, scale, slope_tolerance):
        self.terrain = terrain
        self.config = philosophy_config
        self.scale = scale
        # Map 0-1 slider to max gradient (0.05 to 0.6)
        self.max_slope = 0.05 + slope_tolerance * 0.55

        self.road_graph = nx.Graph()
        self.footprints = []

    def find_anchor(self):
        """Finds a suitable starting point."""
        buildable = self.terrain.get_buildable_mask(self.max_slope)
        h, w = self.terrain.height, self.terrain.width
        cy, cx = h // 2, w // 2

        for r in range(0, min(h, w) // 2, 20):
            for dy in range(-r, r + 1, max(1, r)):
                for dx in range(-r, r + 1, max(1, r)):
                    y, x = cy + dy, cx + dx
                    if 0 <= y < h and 0 <= x < w and buildable[y, x]:
                        return x, y
        return None

    def check_segment_buildable(self, x1, y1, x2, y2, buildable_mask):
        num_points = int(np.hypot(x2 - x1, y2 - y1))
        if num_points == 0: return True

        xs = np.linspace(x1, x2, num_points).astype(int)
        ys = np.linspace(y1, y2, num_points).astype(int)

        h, w = buildable_mask.shape
        valid_indices = (xs >= 0) & (xs < w) & (ys >= 0) & (ys < h)
        if not np.all(valid_indices): return False

        unbuildable_count = np.sum(~buildable_mask[ys, xs])
        if unbuildable_count > num_points * 0.15:
            return False
        return True

    def snap_to_existing(self, nx_pos, ny_pos, snap_dist):
        for n, data in self.road_graph.nodes(data=True):
            ex, ey = data['pos']
            if np.hypot(ex - nx_pos, ey - ny_pos) < snap_dist:
                return False, n, ex, ey
        return True, None, nx_pos, ny_pos

    def generate_grid(self, start_x, start_y):
        self.road_graph.add_node(0, pos=(start_x, start_y))
        buildable = self.terrain.get_buildable_mask(self.max_slope)

        # Adjust block sizes to be much larger, matching reference
        block_w = int(250 / self.scale)
        block_h = int(180 / self.scale)

        node_idx = 1
        queue = [(0, start_x, start_y)]
        directions = [(block_w, 0), (-block_w, 0), (0, block_h), (0, -block_h)]

        max_nodes = 400
        while queue and len(self.road_graph.nodes) < max_nodes:
            parent_id, px, py = queue.pop(0)
            for dx, dy in directions:
                nx_pos, ny_pos = px + dx, py + dy
                is_new, target_id, sx, sy = self.snap_to_existing(nx_pos, ny_pos, min(block_w, block_h) * 0.4)
                if self.check_segment_buildable(px, py, sx, sy, buildable):
                    if is_new:
                        self.road_graph.add_node(node_idx, pos=(sx, sy))
                        self.road_graph.add_edge(parent_id, node_idx)
                        queue.append((node_idx, sx, sy))
                        node_idx += 1
                    elif target_id != parent_id and not self.road_graph.has_edge(parent_id, target_id):
                        self.road_graph.add_edge(parent_id, target_id)


    def generate_radial(self, start_x, start_y):
        self.road_graph.add_node(0, pos=(start_x, start_y))
        buildable = self.terrain.get_buildable_mask(self.max_slope)

        node_idx = 1
        ring_spacing = int(120 / self.scale)
        num_spokes = 8

        for ring in range(1, 5):
            r = ring * ring_spacing
            ring_nodes = []
            for i in range(num_spokes):
                angle = i * (2 * math.pi / num_spokes)
                nx = int(start_x + r * math.cos(angle))
                ny = int(start_y + r * math.sin(angle))

                is_new, target_id, sx, sy = self.snap_to_existing(nx, ny, ring_spacing * 0.4)
                if self.check_segment_buildable(start_x, start_y, sx, sy, buildable):
                    if is_new:
                        self.road_graph.add_node(node_idx, pos=(sx, sy))
                        ring_nodes.append(node_idx)
                        # Connect to center or previous ring
                        self.road_graph.add_edge(0, node_idx)
                        node_idx += 1
                    else:
                        ring_nodes.append(target_id)

            # Connect ring
            for i in range(len(ring_nodes)):
                u = ring_nodes[i]
                v = ring_nodes[(i+1)%len(ring_nodes)]
                if u != v and not self.road_graph.has_edge(u, v):
                    ux, uy = self.road_graph.nodes[u]['pos']
                    vx, vy = self.road_graph.nodes[v]['pos']
                    if self.check_segment_buildable(ux, uy, vx, vy, buildable):
                        self.road_graph.add_edge(u, v)

    def generate_organic(self, start_x, start_y):
        self.road_graph.add_node(0, pos=(start_x, start_y))
        buildable = self.terrain.get_buildable_mask(self.max_slope)

        node_idx = 1
        queue = [(0, start_x, start_y)]

        max_nodes = 300
        step_size = int(100 / self.scale)

        while queue and len(self.road_graph.nodes) < max_nodes:
            parent_id, px, py = queue.pop(0)

            # 3 random branches
            for _ in range(3):
                angle = random.uniform(0, 2 * math.pi)
                nx = int(px + step_size * math.cos(angle))
                ny = int(py + step_size * math.sin(angle))

                is_new, target_id, sx, sy = self.snap_to_existing(nx, ny, step_size * 0.5)
                if self.check_segment_buildable(px, py, sx, sy, buildable):
                    if is_new:
                        self.road_graph.add_node(node_idx, pos=(sx, sy))
                        self.road_graph.add_edge(parent_id, node_idx)
                        queue.append((node_idx, sx, sy))
                        node_idx += 1
                    elif target_id != parent_id and not self.road_graph.has_edge(parent_id, target_id):
                        self.road_graph.add_edge(parent_id, target_id)

    def generate_linear(self, start_x, start_y):
        self.road_graph.add_node(0, pos=(start_x, start_y))
        buildable = self.terrain.get_buildable_mask(self.max_slope)

        node_idx = 1
        spine_length = int(800 / self.scale)
        branch_len = int(150 / self.scale)

        # Central spine
        prev_node = 0
        px, py = start_x, start_y
        for i in range(1, 10):
            nx = px + int(spine_length / 10)
            ny = py
            is_new, target_id, sx, sy = self.snap_to_existing(nx, ny, 10)
            if self.check_segment_buildable(px, py, sx, sy, buildable):
                self.road_graph.add_node(node_idx, pos=(sx, sy))
                self.road_graph.add_edge(prev_node, node_idx)

                # Branches
                for dy in [branch_len, -branch_len]:
                    bx, by = sx, sy + dy
                    if self.check_segment_buildable(sx, sy, bx, by, buildable):
                        self.road_graph.add_node(node_idx+1, pos=(bx, by))
                        self.road_graph.add_edge(node_idx, node_idx+1)
                        node_idx += 1

                prev_node = node_idx
                node_idx += 1
                px, py = sx, sy
            else:
                break


    def generate_blocks_and_footprints(self):
        if not self.road_graph.edges: return

        lines = []
        for u, v in self.road_graph.edges:
            pos_u = self.road_graph.nodes[u]['pos']
            pos_v = self.road_graph.nodes[v]['pos']
            lines.append(LineString([pos_u, pos_v]))

        polygons = list(polygonize(lines))

        self.footprints = []

        if not polygons and lines:
            # If no cycles were found (e.g. linear spine), just buffer the lines as "blocks"
            for line in lines:
                poly = line.buffer(int(50 / self.scale))
                if not poly.is_empty and isinstance(poly, Polygon):
                    polygons.append(poly)

        for poly in polygons:
            # We want slightly smaller footprints relative to the massive blocks
            # But we also want interior subdivision to match the reference image.

            # Subdivide large block polygons into smaller parcels
            area = poly.area
            if area > (200 / self.scale)**2:
                # Basic subdivision: split in half
                min_x, min_y, max_x, max_y = poly.bounds
                mid_x = (min_x + max_x) / 2
                mid_y = (min_y + max_y) / 2

                # Split vertically or horizontally based on aspect ratio
                if (max_x - min_x) > (max_y - min_y):
                    splitter = LineString([(mid_x, min_y - 100), (mid_x, max_y + 100)])
                else:
                    splitter = LineString([(min_x - 100, mid_y), (max_x + 100, mid_y)])

                from shapely.ops import split
                split_polys = split(poly, splitter)
                parcels = list(split_polys.geoms) if hasattr(split_polys, 'geoms') else list(split_polys)
            else:
                parcels = [poly]

            for parcel in parcels:
                # Calculate setback (distance from street)
                setback = int(10 / self.scale)
                if setback <= 0: setback = 1

                footprint = parcel.buffer(-setback)

                if not footprint.is_empty:
                    if isinstance(footprint, Polygon):
                        if footprint.area > (20 / self.scale)**2:
                            self.footprints.append(footprint)
                    elif footprint.geom_type == 'MultiPolygon':
                        for p in footprint.geoms:
                            if p.area > (20 / self.scale)**2:
                                self.footprints.append(p)

    def generate(self):
        anchor = self.find_anchor()
        if not anchor:
            return False

        start_x, start_y = anchor

        philosophy_id = self.config.get('id', 'hippodamian_grid').lower()

        if philosophy_id in ['star_fort', 'baroque_axial', 'garden_city', 'haussmann_boulevard']:
            self.generate_radial(start_x, start_y)
        elif philosophy_id in ['organic_medieval', 'terraced_contour', 'romantic_pastoral', 'dendritic_suburban']:
            self.generate_organic(start_x, start_y)
        elif philosophy_id in ['linear_spine']:
            self.generate_linear(start_x, start_y)
        else:
            self.generate_grid(start_x, start_y)

        self.generate_blocks_and_footprints()
        return True
