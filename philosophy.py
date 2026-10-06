from dataclasses import dataclass
from enum import Enum
from typing import Optional, Dict

class NetworkType(Enum):
    ORTHOGONAL_GRID = "Orthogonal Grid"
    ORTHOGONAL_AXES = "Orthogonal Axes"
    PLAZA_CENTRIC_GRID = "Plaza-centric Grid"
    RADIAL_CONCENTRIC = "Radial Concentric"
    MONUMENTAL_RAYS = "Monumental Rays"
    DUAL_RIVER_GRID = "Dual-River Grid"
    MODULAR_WARDS = "Modular Wards"
    DENSITY_GRID = "Density Grid"
    MILE_SECTION_LINES = "Mile Section Lines"
    RADIAL_ARTERIAL = "Radial Arterial"
    CHAMFERED_GRID = "Chamfered Grid"
    TOPOGRAPHIC_CONTOURS = "Topographic Contours"
    CONTOUR_RIBBONS = "Contour Ribbons"
    CONCENTRIC_PASTORAL = "Concentric Pastoral"
    LINEAR_CORRIDOR = "Linear Corridor"
    ORTHOGONAL_HIGHWAY = "Orthogonal Highway"
    CURVILINEAR_PODS = "Curvilinear Pods"
    RADIAL_WALKABLE = "Radial Walkable"
    CURVILINEAR_SCENIC = "Curvilinear Scenic"

class MaxSlope(Enum):
    GENTLE = 0.45
    MODERATE = 0.70
    STEEP = 1.0
    EXTREME = 2.0

class TerrainAction(Enum):
    CONVERTS_TO_STAIRS = "Converts to stairs; cuts/fills"
    INVALIDATES_IF_BLOCKED = "Invalidates if axes blocked"
    TRUNCATES_AT_CLIFF = "Truncates grid at cliff edges"
    INVALIDATES_ON_BROKEN_SIGHTLINES = "Invalidates on broken sightlines"
    CUTS_THROUGH_MONUMENTAL_RAMPS = "Cuts through; monumental ramps"
    STEPPED_FOUNDATIONS = "Stepped foundations; terraces"
    SKIPS_WARD = "Skips ward placement on slope"
    LEVELS_HILLS = "Levels hills; retains steep cuts"
    BYPASSES_OBSTACLE = "Bypasses obstacle; returns to line"
    CURVED_BYPASS = "Curved bypass; cuts retaining wall"
    INVALIDATES_IF_WARPS = "Invalidates if blocks warp"
    ADAPTS_TO_CONTOURS = "Adapts to contours; uses stairs"
    RUNS_PARALLEL = "Runs parallel; vertical steps"
    CURVES_AROUND_SLOPES = "Curves around slopes; greenbelt"
    TUNNELS_OR_TERMINATES = "Tunnels through; or terminates"
    BUILDINGS_ON_STILTS = "Buildings on stilts; flyovers"
    WINDS_ALONG_VALLEYS = "Winds along valleys; dead-ends"
    ELEVATORS_RAMPS_OR_INVALIDATES = "Elevators/ramps; or invalidates"
    SWEEPING_CURVES = "Sweeping curves; preserves terrain"

@dataclass
class PhilosophyConfig:
    name: str
    network_type: NetworkType
    max_slope: MaxSlope
    terrain_action: TerrainAction

PHILOSOPHIES: Dict[str, PhilosophyConfig] = {
    "Classical Hippodamian Grid": PhilosophyConfig(
        "Classical Hippodamian Grid", NetworkType.ORTHOGONAL_GRID, MaxSlope.MODERATE, TerrainAction.CONVERTS_TO_STAIRS
    ),
    "Ancient Roman Castrum": PhilosophyConfig(
        "Ancient Roman Castrum", NetworkType.ORTHOGONAL_AXES, MaxSlope.MODERATE, TerrainAction.INVALIDATES_IF_BLOCKED
    ),
    "Laws of the Indies (Spanish Colonial)": PhilosophyConfig(
        "Laws of the Indies (Spanish Colonial)", NetworkType.PLAZA_CENTRIC_GRID, MaxSlope.MODERATE, TerrainAction.TRUNCATES_AT_CLIFF
    ),
    "Star Fort / Ideal Renaissance": PhilosophyConfig(
        "Star Fort / Ideal Renaissance", NetworkType.RADIAL_CONCENTRIC, MaxSlope.GENTLE, TerrainAction.INVALIDATES_ON_BROKEN_SIGHTLINES
    ),
    "Baroque Axial / Grand Vista": PhilosophyConfig(
        "Baroque Axial / Grand Vista", NetworkType.MONUMENTAL_RAYS, MaxSlope.MODERATE, TerrainAction.CUTS_THROUGH_MONUMENTAL_RAMPS
    ),
    "Quaker Enlightenment Grid": PhilosophyConfig(
        "Quaker Enlightenment Grid", NetworkType.DUAL_RIVER_GRID, MaxSlope.MODERATE, TerrainAction.STEPPED_FOUNDATIONS
    ),
    "Cellular Ward System": PhilosophyConfig(
        "Cellular Ward System", NetworkType.MODULAR_WARDS, MaxSlope.GENTLE, TerrainAction.SKIPS_WARD
    ),
    "Speculative Utilitarian Grid": PhilosophyConfig(
        "Speculative Utilitarian Grid", NetworkType.DENSITY_GRID, MaxSlope.STEEP, TerrainAction.LEVELS_HILLS
    ),
    "Section-Line Macro Grid": PhilosophyConfig(
        "Section-Line Macro Grid", NetworkType.MILE_SECTION_LINES, MaxSlope.STEEP, TerrainAction.BYPASSES_OBSTACLE
    ),
    "Haussmannian Boulevard": PhilosophyConfig(
        "Haussmannian Boulevard", NetworkType.RADIAL_ARTERIAL, MaxSlope.MODERATE, TerrainAction.CURVED_BYPASS
    ),
    "Cerda Chamfered Superblock": PhilosophyConfig(
        "Cerda Chamfered Superblock", NetworkType.CHAMFERED_GRID, MaxSlope.MODERATE, TerrainAction.INVALIDATES_IF_WARPS
    ),
    "Organic Medieval / Topographic Hilltown": PhilosophyConfig(
        "Organic Medieval / Topographic Hilltown", NetworkType.TOPOGRAPHIC_CONTOURS, MaxSlope.STEEP, TerrainAction.ADAPTS_TO_CONTOURS
    ),
    "Terraced Contour / Hillside Urbanism": PhilosophyConfig(
        "Terraced Contour / Hillside Urbanism", NetworkType.CONTOUR_RIBBONS, MaxSlope.EXTREME, TerrainAction.RUNS_PARALLEL
    ),
    "Garden City Satellite": PhilosophyConfig(
        "Garden City Satellite", NetworkType.CONCENTRIC_PASTORAL, MaxSlope.MODERATE, TerrainAction.CURVES_AROUND_SLOPES
    ),
    "Linear Infrastructure Spine": PhilosophyConfig(
        "Linear Infrastructure Spine", NetworkType.LINEAR_CORRIDOR, MaxSlope.MODERATE, TerrainAction.TUNNELS_OR_TERMINATES
    ),
    "Modernist Superblock": PhilosophyConfig(
        "Modernist Superblock", NetworkType.ORTHOGONAL_HIGHWAY, MaxSlope.MODERATE, TerrainAction.BUILDINGS_ON_STILTS
    ),
    "Dendritic Suburban Sprawl": PhilosophyConfig(
        "Dendritic Suburban Sprawl", NetworkType.CURVILINEAR_PODS, MaxSlope.STEEP, TerrainAction.WINDS_ALONG_VALLEYS
    ),
    "Transit-Oriented Development": PhilosophyConfig(
        "Transit-Oriented Development", NetworkType.RADIAL_WALKABLE, MaxSlope.MODERATE, TerrainAction.ELEVATORS_RAMPS_OR_INVALIDATES
    ),
    "Romantic / Pastoral Landscape Suburb": PhilosophyConfig(
        "Romantic / Pastoral Landscape Suburb", NetworkType.CURVILINEAR_SCENIC, MaxSlope.STEEP, TerrainAction.SWEEPING_CURVES
    ),
}
