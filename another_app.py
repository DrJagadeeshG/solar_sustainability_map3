import streamlit as st
import pandas as pd
import geopandas as gpd
import folium
from streamlit_folium import folium_static
import os
import plotly.graph_objects as go

# Set page configuration
st.set_page_config(
    page_title="Solar Suitability Analysis",
    page_icon="☀️",
    layout="wide",
    initial_sidebar_state="collapsed"
)

# Custom CSS for professional dashboard styling
st.markdown("""
<style>
    .main > div {
        padding-top: 1rem;
    }
    .main-header {
        font-size: 2.2rem;
        color: #FFFFFF;
        text-align: center;
        margin-bottom: 1.5rem;
        font-weight: 600;
    }
    .controls-section {
        background: linear-gradient(135deg, #1e3c72 0%, #2a5298 100%);
        padding: 1.2rem;
        border-radius: 12px;
        margin-bottom: 1.5rem;
        box-shadow: 0 4px 6px rgba(0, 0, 0, 0.1);
    }
    .metric-card {
        background-color: #1E1E1E;
        padding: 1rem;
        border-radius: 8px;
        border-left: 4px solid #4CAF50;
        margin-bottom: 0.5rem;
        box-shadow: 0 2px 4px rgba(0, 0, 0, 0.1);
    }
    .chart-container {
        background-color: #1E1E1E;
        padding: 1rem;
        border-radius: 8px;
        box-shadow: 0 2px 4px rgba(0, 0, 0, 0.1);
        height: 100%;
    }
    .info-card {
        background-color: #1E1E1E;
        padding: 1rem;
        border-radius: 8px;
        box-shadow: 0 2px 4px rgba(0, 0, 0, 0.1);
        margin-bottom: 1rem;
    }
    .section-header {
        color: #FFFFFF;
        font-size: 1.2rem;
        font-weight: 600;
        margin-bottom: 1rem;
        display: flex;
        align-items: center;
    }
    /* Hide Streamlit elements */
    #MainMenu {visibility: hidden;}
    footer {visibility: hidden;}
    .stDeployButton {display: none;}
    .stSpinner {display: none;}
    
    /* Selectbox styling */
    .stSelectbox > div > div {
        background-color: rgba(255, 255, 255, 0.1);
        color: white;
        border-radius: 6px;
    }
    
    /* Compact spacing */
    .block-container {
        padding-top: 1rem;
        padding-bottom: 1rem;
    }
</style>
""", unsafe_allow_html=True)

# Optimized cache functions with TTL and compression
@st.cache_data(ttl=3600, show_spinner="Loading geographic data...", max_entries=3)
def load_and_preprocess_shapefile(file_path):
    """Load shapefile with optimized settings"""
    try:
        # Load with specific optimizations
        gdf = gpd.read_file(file_path, engine='pyogrio')  # Faster engine if available
    except:
        try:
            gdf = gpd.read_file(file_path, engine='fiona')  # Fallback
        except:
            gdf = gpd.read_file(file_path)  # Default
    
    # Optimize geometry for faster rendering
    gdf = gdf.to_crs('EPSG:4326')  # Ensure proper CRS
    
    # Preprocess data for faster filtering
    processed_data = {
        'gdf': gdf,
        'states': ["All States"] + sorted([str(s) for s in gdf["NAME_1"].unique() if s is not None and str(s) != "nan"]),
        'districts_by_state': {},
        'categories': [col for col in gdf.columns if col in ['Adaptation', 'Mitigation', 'Replacment', 'General_SI']],
        'bounds': gdf.geometry.total_bounds
    }
    
    # Pre-calculate districts for each state
    for state in processed_data['states'][1:]:
        state_districts = gdf[gdf["NAME_1"] == state]["NAME_2"].unique()
        processed_data['districts_by_state'][state] = ["All Districts"] + sorted([str(d) for d in state_districts if d is not None and str(d) != "nan"])
    
    return processed_data

@st.cache_data(ttl=3600, show_spinner=False)
def get_category_colors():
    """Pre-cache all color mappings"""
    return {
        "Adaptation": {
            "No Data": "#FFFFFF",
            "Very Highly Suitable": "#2E7D32",
            "Highly Suitable": "#66BB6A",
            "Moderately Suitable": "#FFEB3B",
            "Less Suitable": "#F44336"
        },
        "Mitigation": {
            "Very High Suitable": "#2E7D32",
            "Highly Suitable": "#66BB6A",
            "Moderately Suitable": "#FFEB3B",
            "Less Suitable": "#D32F2F"
        },
        "Replacment": {
            "No Data": "#FFFFFF",
            "Highly Suitable (On Grid Community Wells)": "#2E7D32",
            "Highly Suitable (Community Wells)": "#4CAF50",
            "Highly Suitable (On Grid)": "#66BB6A",
            "Highly Suitable": "#81C784",
            "Moderately Suitable": "#FFEB3B",
            "Less Suitable": "#8D6E63"
        },
        "General_SI": {
            "No Data": "#FFFFFF",
            "Highly Suitable (Adaptation )": "#9C27B0",
            "Highly Suitable (Adaptation + Mitigation)": "#2196F3",
            "Highly Suitable (Adaptation + Mitigation + On Grid": "#1976D2",
            "Highly Suitable (Adaptation + On Grid Community We": "#81D4FA",
            "Highly Suitable (Adaptation + On Grid Replacement)": "#B39DDB",
            "Highly Suitable (Mitigation)": "#4DB6AC",
            "Highly Suitable (Mitigation + On Grid Community We": "#00695C",
            "Highly Suitable (Mitigation + On Grid Replacement)": "#26A69A",
            "Highly Suitable (On Grid Community Wells)": "#66BB6A",
            "Highly Suitable (On Grid Replacement)": "#A5D6A7",
            "Moderately Suitable": "#FFEB3B",
            "Less Suitable": "#F44336"
        }
    }

def get_parameter_values_optimized(gdf, state, district, category):
    """Optimized parameter calculation without caching for speed"""
    # Fast filtering using pandas operations
    filtered_data = gdf.copy()
    if state != "All States":
        filtered_data = filtered_data[filtered_data["NAME_1"] == state]
    if district != "All Districts":
        filtered_data = filtered_data[filtered_data["NAME_2"] == district]
    
    # Define parameter mapping - reduced set for speed
    PARAMETER_MAPPING = {
        "Solar Radiance": "aridity",
        "Cropping Intensity (%)": "CI_____1",
        "Irrigation Coverage (%)": "Irrig_cov_",
        "Cultivated Land (% of total)": "C_Land_Rc",
        "Groundwater Development (%)": "GW_dev_sta",
        "Farmers Average Area (ha)": "C_Ag_All",
        "Small & Marginal Holdings (%)": "C_S_H",
        "Aridity Index": "aridity"
    }
    
    # Fast parameter calculation
    parameter_values = {}
    for param_name, column_name in PARAMETER_MAPPING.items():
        if column_name in filtered_data.columns:
            values = filtered_data[column_name].dropna()
            if len(values) > 0 and values.dtype in ['float64', 'int64']:
                parameter_values[param_name] = f"{values.mean():.2f}"
            else:
                parameter_values[param_name] = "N/A"
        else:
            parameter_values[param_name] = "N/A"
    
    # Calculate statistics here to avoid extra function calls
    stats_dict = {}
    if category in filtered_data.columns:
        stats_data = filtered_data[category].value_counts()
        stats_dict = stats_data.to_dict()
    
    return parameter_values, filtered_data, stats_dict

# Categories mapping
categories = {
    "Adaptation": "Adaptation",
    "Mitigation": "Mitigation", 
    "Replacment": "Replacement",
    "General_SI": "General SI"
}

# Try to find the shapefile
shapefile_path = "Solar_Suitability_layer.shp"
for file in os.listdir('.'):
    if file.endswith('.shp'):
        shapefile_path = file
        break

# Load data with progress indicator
if 'processed_data' not in st.session_state:
    st.session_state.processed_data = load_and_preprocess_shapefile(shapefile_path)
    st.session_state.color_mappings = get_category_colors()

processed_data = st.session_state.processed_data

if processed_data is not None:
    # Dashboard Header
    st.markdown('<h1 class="main-header">☀️ Solar Suitability Analysis Dashboard</h1>', unsafe_allow_html=True)
    
    # Top Controls Section
    st.markdown('<div class="controls-section">', unsafe_allow_html=True)
    filter_col1, filter_col2, filter_col3 = st.columns([1, 1, 1])
    
    with filter_col1:
        st.markdown("**🌍 Select State**")
        selected_state = st.selectbox("State", processed_data['states'], label_visibility="collapsed")
    
    with filter_col2:
        st.markdown("**🏘️ Select District**")
        # Fast district lookup from preprocessed data
        if selected_state != "All States" and selected_state in processed_data['districts_by_state']:
            districts = processed_data['districts_by_state'][selected_state]
        else:
            districts = ["All Districts"]
        selected_district = st.selectbox("District", districts, label_visibility="collapsed")
    
    with filter_col3:
        st.markdown("**📊 Select Category**")
        selected_category = st.selectbox(
            "Category",
            list(categories.keys()),
            format_func=lambda x: categories[x],
            label_visibility="collapsed"
        )
    
    st.markdown('</div>', unsafe_allow_html=True)
    
    # Fast data processing
    parameter_values, filtered_gdf, stats_dict = get_parameter_values_optimized(
        processed_data['gdf'], selected_state, selected_district, selected_category
    )
    
    # Main Dashboard Layout - 3 columns
    left_col, center_col, right_col = st.columns([1, 2, 1])
    
    # LEFT COLUMN - Key Metrics & Parameters
    with left_col:
        st.markdown('<div class="section-header">📋 Key Parameters</div>', unsafe_allow_html=True)
        
        # Display parameters with icons
        icons = {
            "Solar Radiance": "☀️", "Cropping Intensity (%)": "🌾", "Irrigation Coverage (%)": "💧",
            "Cultivated Land (% of total)": "🌾", "Groundwater Development (%)": "💧",
            "Farmers Average Area (ha)": "👨‍🌾", "Small & Marginal Holdings (%)": "👨‍🌾", "Aridity Index": "☀️"
        }
        
        for param, value in parameter_values.items():
            icon = icons.get(param, "📊")
            st.markdown(f"""
            <div class="metric-card">
                <div style="display: flex; justify-content: space-between; align-items: center;">
                    <div style="font-size: 0.85rem; color: #CCCCCC;">
                        {icon} {param}
                    </div>
                    <div style="font-size: 1.1rem; font-weight: bold; color: #4CAF50;">
                        {value}
                    </div>
                </div>
            </div>
            """, unsafe_allow_html=True)
    
    # CENTER COLUMN - Optimized Map
    with center_col:
        st.markdown('<div class="chart-container">', unsafe_allow_html=True)
        st.markdown('<div class="section-header">🗺️ Solar Suitability Map</div>', unsafe_allow_html=True)
        
        if not filtered_gdf.empty:
            # Always show full India map when no specific filters are applied
            if selected_state == "All States" and selected_district == "All Districts":
                # India's full geographic bounds
                center = [20.5937, 78.9629]  # Geographic center of India
                zoom_level = 4  # Reduced zoom to show full country
            else:
                # For specific selections, focus on that area
                bounds = filtered_gdf.geometry.total_bounds
                center = [(bounds[1] + bounds[3]) / 2, (bounds[0] + bounds[2]) / 2]
                
                # Calculate area to determine appropriate zoom
                lat_diff = bounds[3] - bounds[1]
                lon_diff = bounds[2] - bounds[0]
                area = lat_diff * lon_diff
                
                if area > 25:  # Very large area (multiple states)
                    zoom_level = 5
                elif area > 4:  # Large area (state level)
                    zoom_level = 6
                else:  # Smaller area (district level)
                    zoom_level = 7
            
            # Optimized map creation
            m = folium.Map(location=center, zoom_start=zoom_level, tiles="CartoDB dark_matter")
            
            # Fast color mapping
            category_colors = st.session_state.color_mappings.get(selected_category, {})
            
            # Optimized style function
            def style_function(feature):
                cat_val = feature['properties'].get(selected_category)
                if cat_val and str(cat_val) in category_colors:
                    color = category_colors[str(cat_val)]
                else:
                    color = '#BBBBBB'
                
                return {
                    'fillColor': color,
                    'color': 'black',
                    'weight': 1,
                    'fillOpacity': 0.7
                }
            
            # Add optimized GeoJSON layer - simplified for large datasets
            if len(filtered_gdf) > 500:  # For large datasets, skip tooltips
                folium.GeoJson(
                    filtered_gdf.to_json(),
                    style_function=style_function
                ).add_to(m)
            else:
                folium.GeoJson(
                    filtered_gdf.to_json(),
                    style_function=style_function,
                    tooltip=folium.GeoJsonTooltip(
                        fields=["NAME_2", selected_category],
                        aliases=["District", categories[selected_category]],
                        localize=True
                    )
                ).add_to(m)
            
            # Display map
            folium_static(m, height=450)
        else:
            st.warning("No data available for the selected filters.")
        
        st.markdown('</div>', unsafe_allow_html=True)
    
    # RIGHT COLUMN - Fast Statistics
    with right_col:
        st.markdown('<div class="chart-container">', unsafe_allow_html=True)
        st.markdown('<div class="section-header">📈 Distribution</div>', unsafe_allow_html=True)
        
        if stats_dict:
            labels = list(stats_dict.keys())
            values = list(stats_dict.values())
            colors = [st.session_state.color_mappings.get(selected_category, {}).get(str(label), "#BBBBBB") for label in labels]
            
            fig = go.Figure(data=[go.Pie(
                labels=labels,
                values=values,
                marker=dict(colors=colors),
                textinfo='label+percent',
                textposition='auto',
                textfont=dict(size=8, color='white'),
                showlegend=False,
                hovertemplate='<b>%{label}</b><br>Count: %{value}<br>Percentage: %{percent}<extra></extra>'
            )])
            
            fig.update_layout(
                paper_bgcolor='rgba(0,0,0,0)',
                plot_bgcolor='rgba(0,0,0,0)',
                font=dict(color='white', size=8),
                margin=dict(t=20, b=20, l=20, r=20),
                height=280
            )
            
            st.plotly_chart(fig, use_container_width=True, config={'displayModeBar': False})
        else:
            st.info("No data to display")
        
        st.markdown('</div>', unsafe_allow_html=True)
        
        # Fast Location Info
        st.markdown('<div class="info-card">', unsafe_allow_html=True)
        st.markdown('<div class="section-header">📍 Selection Info</div>', unsafe_allow_html=True)
        
        info_items = [
            ("🏛️ State", selected_state if selected_state != "All States" else "All"),
            ("🏘️ District", selected_district if selected_district != "All Districts" else "All"),
            ("📊 Category", categories[selected_category]),
            ("📋 Features", str(len(filtered_gdf)))
        ]
        
        for label, value in info_items:
            st.markdown(f"""
            <div style="display: flex; justify-content: space-between; padding: 0.3rem 0; border-bottom: 1px solid #333;">
                <span style="color: #CCCCCC; font-size: 0.85rem;">{label}</span>
                <span style="color: #4CAF50; font-weight: bold; font-size: 0.85rem;">{value}</span>
            </div>
            """, unsafe_allow_html=True)
        
        st.markdown('</div>', unsafe_allow_html=True)

else:
    st.error(f"Could not load shapefile from {shapefile_path}")
    st.subheader("Troubleshooting Information")
    st.write(f"Current working directory: {os.getcwd()}")
    st.write("Files in current directory:")
    st.write([f for f in os.listdir('.') if f.endswith('.shp') or f.endswith('.dbf') or f.endswith('.shx')])