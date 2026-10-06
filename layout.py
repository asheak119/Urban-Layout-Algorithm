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

        for r in range(0, min(h, w) // 2, 10):
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
        if unbuildable_count > num_points * 0.1:
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

        block_w = int(120 / self.scale)
        block_h = int(120 / self.scale)

        if 'elongated' in self.config['block_pattern'].lower() or 'narrow' in self.config['block_pattern'].lower():
            block_h = int(60 / self.scale)
        elif 'macro' in self.config['topology'].lower():
            block_w = block_h = int(300 / self.scale)

        node_idx = 1
        queue = [(0, start_x, start_y)]
        directions = [(block_w, 0), (-block_w, 0), (0, block_h), (0, -block_h)]

        if 'chamfered' in self.config['topology'].lower() or 'diagonal' in self.config['topology'].lower():
            directions.extend([(block_w, block_h), (-block_w, -block_h), (block_w, -block_h), (-block_w, block_h)])

        max_nodes = 800
        while queue and len(self.road_graph.nodes) < max_nodes:
            parent_id, px, py = queue.pop(0)
            for dx, dy in directions:
                nx_pos, ny_pos = px + dx, py + dy
                is_new, target_id, sx, sy = self.snap_to_existing(nx_pos, ny_pos, min(block_w, block_h) * 0.3)
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
        center_id = 0

        rings = 4
        spokes = 8
        ring_spacing = int(100 / self.scale)

        if 'star fort' in self.config['name'].lower():
            rings = 3
            spokes = 6

        ring_nodes = []
        for r in range(1, rings + 1):
            radius = r * ring_spacing
            current_ring = []
            for s in range(spokes):
                angle = s * (2 * math.pi / spokes)
                nx_pos = start_x + radius * math.cos(angle)
                ny_pos = start_y + radius * math.sin(angle)

                is_new, target_id, sx, sy = self.snap_to_existing(nx_pos, ny_pos, ring_spacing * 0.3)
                if self.check_segment_buildable(start_x, start_y, sx, sy, buildable):
                    if is_new:
                        self.road_graph.add_node(node_idx, pos=(sx, sy))
                        # Connect to center or previous ring
                        if r == 1:
                            self.road_graph.add_edge(center_id, node_idx)
                        else:
                            # connect to corresponding spoke on prev ring
                            prev_node = ring_nodes[r-2][s]
                            if prev_node is not None:
                                self.road_graph.add_edge(prev_node, node_idx)

                        current_ring.append(node_idx)
                        node_idx += 1
                    else:
                        current_ring.append(target_id)
                else:
                    current_ring.append(None)
            ring_nodes.append(current_ring)

            # Connect ring
            for s in range(spokes):
                n1 = current_ring[s]
                n2 = current_ring[(s + 1) % spokes]
                if n1 is not None and n2 is not None:
                    pos1 = self.road_graph.nodes[n1]['pos']
                    pos2 = self.road_graph.nodes[n2]['pos']
                    if self.check_segment_buildable(pos1[0], pos1[1], pos2[0], pos2[1], buildable):
                        self.road_graph.add_edge(n1, n2)

    def generate_contour(self, start_x, start_y):
        self.road_graph.add_node(0, pos=(start_x, start_y))
        buildable = self.terrain.get_buildable_mask(self.max_slope)

        step_len = int(30 / self.scale)
        node_idx = 1
        queue = [(0, start_x, start_y, None)]

        max_nodes = 500
        while queue and len(self.road_graph.nodes) < max_nodes:
            parent_id, px, py, dir_angle = queue.pop(0)

            # Follow contour: perpendicular to gradient
            py_int, px_int = int(py), int(px)
            if 0 <= py_int < self.terrain.height and 0 <= px_int < self.terrain.width:
                grad_dir = self.terrain.gradient_dir[py_int, px_int]
                contour_dirs = [grad_dir + math.pi/2, grad_dir - math.pi/2]

                # occasional switchback (up/down slope)
                if random.random() < 0.1:
                    contour_dirs.append(grad_dir + (math.pi if random.random() < 0.5 else 0))

                for angle in contour_dirs:
                    if dir_angle is not None and abs(angle - dir_angle) > math.pi/2 and abs(angle - dir_angle) < 3*math.pi/2:
                        continue # Don't go sharply back

                    nx_pos = px + step_len * math.cos(angle)
                    ny_pos = py + step_len * math.sin(angle)

                    is_new, target_id, sx, sy = self.snap_to_existing(nx_pos, ny_pos, step_len * 0.5)
                    if self.check_segment_buildable(px, py, sx, sy, buildable):
                        if is_new:
                            self.road_graph.add_node(node_idx, pos=(sx, sy))
                            self.road_graph.add_edge(parent_id, node_idx)
                            queue.append((node_idx, sx, sy, angle))
                            node_idx += 1
                        elif target_id != parent_id and not self.road_graph.has_edge(parent_id, target_id):
                            self.road_graph.add_edge(parent_id, target_id)

    def generate_organic(self, start_x, start_y):
        self.road_graph.add_node(0, pos=(start_x, start_y))
        buildable = self.terrain.get_buildable_mask(self.max_slope)

        step_len = int(40 / self.scale)
        node_idx = 1
        queue = [(0, start_x, start_y, random.uniform(0, 2*math.pi))]

        max_nodes = 600
        while queue and len(self.road_graph.nodes) < max_nodes:
            parent_id, px, py, current_angle = queue.pop(0)

            # Branching
            num_branches = random.randint(1, 3)
            for _ in range(num_branches):
                angle = current_angle + random.uniform(-math.pi/4, math.pi/4)
                if random.random() < 0.2: angle += math.pi/2 # Sharp turn

                nx_pos = px + step_len * math.cos(angle)
                ny_pos = py + step_len * math.sin(angle)

                is_new, target_id, sx, sy = self.snap_to_existing(nx_pos, ny_pos, step_len * 0.4)
                if self.check_segment_buildable(px, py, sx, sy, buildable):
                    if is_new:
                        self.road_graph.add_node(node_idx, pos=(sx, sy))
                        self.road_graph.add_edge(parent_id, node_idx)
                        queue.append((node_idx, sx, sy, angle))
                        node_idx += 1
                    elif target_id != parent_id and not self.road_graph.has_edge(parent_id, target_id):
                        self.road_graph.add_edge(parent_id, target_id)

    def generate_linear(self, start_x, start_y):
        self.road_graph.add_node(0, pos=(start_x, start_y))
        buildable = self.terrain.get_buildable_mask(self.max_slope)

        step_len = int(100 / self.scale)
        node_idx = 1

        # Primary axis
        main_angle = random.uniform(0, math.pi)
        px, py = start_x, start_y

        spine_nodes = [0]
        # Grow spine forward and backward
        for angle in [main_angle, main_angle + math.pi]:
            curr_x, curr_y = start_x, start_y
            parent_id = 0
            for _ in range(15):
                nx_pos = curr_x + step_len * math.cos(angle)
                ny_pos = curr_y + step_len * math.sin(angle)
                is_new, target_id, sx, sy = self.snap_to_existing(nx_pos, ny_pos, step_len * 0.2)
                if self.check_segment_buildable(curr_x, curr_y, sx, sy, buildable):
                    if is_new:
                        self.road_graph.add_node(node_idx, pos=(sx, sy))
                        self.road_graph.add_edge(parent_id, node_idx)
                        spine_nodes.append(node_idx)
                        parent_id = node_idx
                        curr_x, curr_y = sx, sy
                        node_idx += 1
                    else:
                        break
                else:
                    break

        # Transverse branches
        queue = []
        for sn in spine_nodes:
            pos = self.road_graph.nodes[sn]['pos']
            queue.append((sn, pos[0], pos[1], main_angle + math.pi/2))
            queue.append((sn, pos[0], pos[1], main_angle - math.pi/2))

        max_nodes = 500
        while queue and len(self.road_graph.nodes) < max_nodes:
            parent_id, px, py, angle = queue.pop(0)
            nx_pos = px + (step_len*0.6) * math.cos(angle)
            ny_pos = py + (step_len*0.6) * math.sin(angle)

            is_new, target_id, sx, sy = self.snap_to_existing(nx_pos, ny_pos, step_len * 0.2)
            if self.check_segment_buildable(px, py, sx, sy, buildable):
                if is_new:
                    self.road_graph.add_node(node_idx, pos=(sx, sy))
                    self.road_graph.add_edge(parent_id, node_idx)
                    queue.append((node_idx, sx, sy, angle))
                    node_idx += 1
                elif target_id != parent_id and not self.road_graph.has_edge(parent_id, target_id):
                    self.road_graph.add_edge(parent_id, target_id)

    def generate_blocks_and_footprints(self):
        if not self.road_graph.edges: return

        lines = []
        for u, v in self.road_graph.edges:
            pos_u = self.road_graph.nodes[u]['pos']
            pos_v = self.road_graph.nodes[v]['pos']
            lines.append(LineString([pos_u, pos_v]))

        polygons = list(polygonize(lines))

        self.footprints = []
        setback = int(4 / self.scale)
        if setback <= 0: setback = 1

        # Adjust density/setback based on philosophy
        if 'low' in self.config['density'].lower(): setback *= 2
        elif 'high' in self.config['density'].lower(): setback = 1

        for poly in polygons:
            footprint = poly.buffer(-setback)
            if not footprint.is_empty:
                if isinstance(footprint, Polygon):
                    if footprint.area > (15 / self.scale)**2:
                        self.footprints.append(footprint)
                elif footprint.geom_type == 'MultiPolygon':
                    for p in footprint.geoms:
                        if p.area > (15 / self.scale)**2:
                            self.footprints.append(p)

    def generate(self):
        anchor = self.find_anchor()
        if not anchor:
            return False

        start_x, start_y = anchor
        topology = self.config['topology'].lower()

        if 'radial' in topology or 'concentric' in topology or 'radiating' in topology:
            self.generate_radial(start_x, start_y)
        elif 'contour' in topology or 'topographic' in topology:
            self.generate_contour(start_x, start_y)
        elif 'organic' in topology or 'curvilinear' in topology or 'dendritic' in topology or 'web-like' in topology or 'tree-like' in topology:
            self.generate_organic(start_x, start_y)
        elif 'linear' in topology or 'axial' in topology or 'diagonal' in topology or 'boulevard' in topology:
            self.generate_linear(start_x, start_y)
        else:
            self.generate_grid(start_x, start_y)

        self.generate_blocks_and_footprints()
        return True
