import plotly.graph_objects as go
import numpy as np
from PIL import Image

def render_layout_plotly(terrain, layout_engine):
    """Renders the terrain, roads, and building footprints as an interactive Plotly figure."""

    # We will use an empty layout with the image as the background
    fig = go.Figure()

    # Image background
    # Plotly needs the image as a PIL image or base64. We can use add_layout_image
    fig.add_layout_image(
        dict(
            source=terrain.image,
            xref="x",
            yref="y",
            x=0,
            y=terrain.height, # Top-left corner
            sizex=terrain.width,
            sizey=terrain.height,
            sizing="stretch",
            opacity=1.0,
            layer="below"
        )
    )

    # Configure axes to match the image coordinate system
    fig.update_xaxes(showgrid=False, range=[0, terrain.width], visible=False)
    fig.update_yaxes(showgrid=False, range=[0, terrain.height], scaleanchor="x", scaleratio=1, visible=False)

    # Plot Footprints
    footprint_x = []
    footprint_y = []

    for footprint in layout_engine.footprints:
        x, y = footprint.exterior.xy
        footprint_x.extend(list(x) + [None])
        footprint_y.extend(list(terrain.height - np.array(y)) + [None]) # Flip Y

    fig.add_trace(go.Scatter(
        x=footprint_x,
        y=footprint_y,
        fill="toself",
        fillcolor="rgba(160, 64, 48, 0.8)",
        line=dict(color="black", width=1),
        mode="lines",
        hoverinfo="none",
        name="Buildings"
    ))

    # Plot Roads
    road_x = []
    road_y = []
    for u, v in layout_engine.road_graph.edges:
        pos_u = layout_engine.road_graph.nodes[u]['pos']
        pos_v = layout_engine.road_graph.nodes[v]['pos']
        road_x.extend([pos_u[0], pos_v[0], None])
        road_y.extend([terrain.height - pos_u[1], terrain.height - pos_v[1], None]) # Flip Y

    fig.add_trace(go.Scatter(
        x=road_x,
        y=road_y,
        mode="lines",
        line=dict(color="black", width=3),
        hoverinfo="none",
        name="Roads"
    ))

    fig.update_layout(
        margin=dict(l=0, r=0, t=0, b=0),
        plot_bgcolor="white",
        width=800,
        height=int(800 * (terrain.height / terrain.width))
    )

    return fig
