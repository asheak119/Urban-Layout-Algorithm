import streamlit as st
import numpy as np
from PIL import Image
import matplotlib.pyplot as plt
import networkx as nx

from philosophy import PHILOSOPHIES
from engine import CityGenerator

st.set_page_config(page_title="Procedural Urban Planning Engine", layout="wide")

st.title("City Generation Algorithmic Engine")
st.markdown("Generates urban layouts from height maps based on distinct architectural philosophies.")

st.sidebar.header("Input & Parameters")

# 1. Height Map Upload
uploaded_file = st.sidebar.file_uploader("Upload Height Map Image (Grayscale)", type=["png", "jpg", "jpeg"])

# 2. Philosophy Selection
philosophy_name = st.sidebar.selectbox(
    "Design Philosophy",
    options=list(PHILOSOPHIES.keys())
)

# 3. Slope Tolerance Slider
slope_tolerance = st.sidebar.slider(
    "Slope Tolerance (Cliff Threshold)",
    min_value=0.1, max_value=5.0, value=1.0, step=0.1,
    help="Low: Strict realistic tolerance. High: Permissive tolerance."
)

# 4. Scale Specification
scale = st.sidebar.number_input(
    "Map Scale (meters per pixel)",
    min_value=0.1, max_value=100.0, value=1.0, step=0.1
)

if uploaded_file is not None:
    # Process image
    img = Image.open(uploaded_file).convert('L')

    # Standardize height map (normalize between 0 and 1)
    img_array = np.array(img)
    height_map = img_array / 255.0

    col1, col2 = st.columns(2)

    with col1:
        st.subheader("Input Height Map")
        fig_hm, ax_hm = plt.subplots()
        cax = ax_hm.imshow(height_map, cmap='terrain')
        fig_hm.colorbar(cax, ax=ax_hm)
        ax_hm.axis('off')
        st.pyplot(fig_hm)

    with col2:
        if st.sidebar.button("Generate City"):
            with st.spinner("Executing Procedural Generation Pipeline..."):
                try:
                    generator = CityGenerator(
                        height_map=height_map,
                        philosophy_name=philosophy_name,
                        slope_tolerance=slope_tolerance,
                        scale=scale
                    )
                    results = generator.generate()

                    st.subheader(f"Generated Layout: {philosophy_name}")

                    # Visualization
                    fig_out, ax_out = plt.subplots(figsize=(8, 8))

                    # Background: Height map faintly
                    ax_out.imshow(height_map, cmap='terrain', alpha=0.5)

                    # Draw Buildings
                    for poly in results['buildings']:
                        x, y = poly.exterior.xy
                        ax_out.fill(x, y, alpha=0.5, fc='brown', ec='black')

                    # Draw Road Network
                    G = results['full_network']
                    pos = nx.get_node_attributes(G, 'pos')

                    # Primary roads
                    primary_edges = []
                    secondary_edges = []

                    for u, v in G.edges():
                        # Just a simple check for visualization
                        if G.nodes[u].get('type') == 'arterial' and G.nodes[v].get('type') == 'arterial':
                            primary_edges.append((u, v))
                        else:
                            secondary_edges.append((u, v))

                    nx.draw_networkx_edges(G, pos, edgelist=primary_edges, width=2.0, edge_color='black', ax=ax_out)
                    nx.draw_networkx_edges(G, pos, edgelist=secondary_edges, width=1.0, edge_color='gray', ax=ax_out)

                    # Draw Anchors
                    for anchor in results['anchors']:
                        ax_out.plot(anchor[1], anchor[0], 'ro', markersize=8, markeredgecolor='white')

                    ax_out.axis('off')
                    st.pyplot(fig_out)

                    st.success("Generation completed successfully!")

                    with st.expander("Customization (Post-Generation)"):
                        st.write("Post-generation layout customization tools would go here.")
                        st.button("Regenerate Road Layout")

                except Exception as e:
                    st.error(f"Generation failed: {str(e)}")

else:
    st.info("Please upload a height map image to begin.")