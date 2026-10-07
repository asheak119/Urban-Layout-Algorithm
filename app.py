import streamlit as st
import configparser
from PIL import Image
import numpy as np

# Load philosophies
def load_philosophies(filepath="philosophies_config.txt"):
    config = configparser.RawConfigParser()
    config.read(filepath)
    philosophies = {}
    for section in config.sections():
        phil_id = config.get(section, 'id', fallback=section)
        philosophies[phil_id] = {
            'id': phil_id,
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
    st.set_page_config(page_title="Procedural Urban Layout Generator", layout="wide")
    st.title("Procedural Urban Layout Generator")

    # Load configurations
    philosophies = load_philosophies()
    philosophy_options = {v['name']: k for k, v in philosophies.items()}

    # Sidebar for parameters
    st.sidebar.header("Configuration")

    uploaded_file = st.sidebar.file_uploader("Upload Height Map", type=["jpg", "jpeg", "png"])

    st.sidebar.subheader("Terrain Parameters")
    water_threshold = st.sidebar.slider("Water Threshold", min_value=0.0, max_value=1.0, value=0.1, step=0.01)

    st.sidebar.subheader("Urban Parameters")
    world_scale = st.sidebar.number_input("World Scale (meters per pixel)", min_value=1.0, value=10.0, step=1.0)
    slope_tolerance = st.sidebar.slider("Slope Tolerance", min_value=0.0, max_value=1.0, value=0.5, step=0.01, help="0.0: Strict (Civil engineering realism), 1.0: Permissive (Game-engine style)")

    selected_philosophy_name = st.sidebar.selectbox("Design Philosophy", options=list(philosophy_options.keys()))
    selected_philosophy_id = philosophy_options[selected_philosophy_name]

    # Show description
    st.sidebar.markdown(f"**Description:** {philosophies[selected_philosophy_id]['terrain_behavior']}")

    if uploaded_file is not None:
        image = Image.open(uploaded_file)
        st.image(image, caption="Uploaded Height Map")

        if st.button("Generate Layout"):
            with st.spinner("Processing Terrain..."):
                from terrain import TerrainProcessor
                from layout import LayoutEngine
                from render import render_layout_plotly

                tp = TerrainProcessor(image)
                tp.calculate_water_mask(threshold=water_threshold)
                tp.calculate_gradients()

            with st.spinner("Generating Layout..."):
                config = philosophies[selected_philosophy_id]
                le = LayoutEngine(tp, config, scale=world_scale, slope_tolerance=slope_tolerance)
                success = le.generate()

            if success:
                with st.spinner("Rendering..."):
                    from render import render_layout_plotly
                    fig = render_layout_plotly(tp, le)
                    st.plotly_chart(fig, use_container_width=True)
            else:
                st.error("Failed to generate layout. Could not find a suitable anchor point.")
    else:
        st.info("Please upload a height map to begin.")

if __name__ == "__main__":
    main()
