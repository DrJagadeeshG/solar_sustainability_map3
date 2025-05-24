import streamlit as st
import pandas as pd
import geopandas as gpd
import folium
from streamlit_folium import folium_static
import os
import matplotlib.pyplot as plt
import numpy as np

# Import the legend component for colors
try:
    from legend_component import get_category_colors
except ImportError:
    def get_category_colors(category):
        return {}

# Set page configuration
st.set_page_config(
    page_title="Solar Suitability Dashboard",
    page_icon="☀️",
    layout="wide"
)

# Minimal, clean CSS
st.markdown("""
<style>
    .main > div {
        padding: 0.5rem;
    }
    .dashboard-title {
        font-size: 2.2rem;
        color: #FFD700;
        text-align: center;
        margin-bottom: 1rem;
        font-weight: bold;
    }
    .filter-section {
        background-color: #2C3E50;
        padding: 1rem;
        border-radius: 8px;
        margin-bottom: 1rem;
    }
    .section-header {
        color: white;
        font-size: 1.1rem;
        font-weight: bold;
        margin-bottom: 0.5rem;
    }
    .compact-metric {
        background-color: #34495E;
        padding: 0.4rem 0.6rem;
        border-radius: 6px;
        margin-bottom: 0.3rem;
        display: flex;
        justify-content: space-between;
        align-items: center;
    }
    .metric-name {
        color: white;
        font-size: 0.85rem;
    }
    .metric-value {
        color: #F39C12;
        font-weight: bold;
        font-size: 0.85rem;
    }
    .stSelectbox label {
        color: white !important;
        font-weight: bold;
    }
    #MainMenu {visibility: hidden;}
    footer {visibility: hidden;}
    .stDeployButton {visibility: hidden;}
</style>
""", unsafe_allow_html=True)

# Cache data loading
@st.cache_data(ttl=3600)
def load_shapefile(file_path):
    try:
        gdf = gpd.read_file(file_path)
        if len(gdf) > 100:
            gdf.geometry = gdf.geometry.simplify(0.001, preserve_topology=False)
        return gdf
    except Exception as e:
        st.error(f"Error loading shapefile: {e}")
        return None

# Parameter mapping
PARAMETER_MAPPING = {
    "Solar Radiance": "aridity",
    "Cropping Intensity (%)": "CI_____1", 
    "Irrigation Coverage (%)": "Irrig_cov_",
    "Irrigation Water Requirement": "ration__cu",
    "Cultivated Land (% of total)": "C_Land_Rc",
    "Pump Energy Source (Electric)": "C_E_FC",
    "Energy Subsidy": "C_Others",
    "Groundwater Development (%)": "GW_dev_sta",
    "Aquifer Depth (mbgl)": "C_Aqua_C",
    "Surface Water Body (ha)": "C_SWC",
    "Small & Marginal Holdings (%)": "C_S_H",
    "Farmers Average Area (ha)": "C_Ag_All",
    "Land Fragmentation": "C_F_L",
    "Aridity Index": "aridity"
}

categories = {
    "Adaptation": "Adaptation",
    "Mitigation": "Mitigation", 
    "Replacment": "Replacement",
    "General_SI": "General SI"
}

def calculate_statistics(gdf, category):
    if category not in gdf.columns:
        return None
    
    stats = {}
    if gdf[category].dtype == 'object':
        value_counts = gdf[category].value_counts()
        total = len(gdf)
        
        stats['counts'] = {}
        for value, count in value_counts.items():
            if value is not None and str(value) != "nan":
                percentage = (count / total) * 100
                stats['counts'][value] = {
                    'count': int(count),
                    'percentage': round(percentage, 2)
                }
    return stats

def get_parameter_values(gdf, selected_state, selected_district):
    filtered_data = gdf.copy()
    
    if selected_state != "All States":
        filtered_data = filtered_data[filtered_data["NAME_1"] == selected_state]
    
    if selected_district != "All Districts":
        filtered_data = filtered_data[filtered_data["NAME_2"] == selected_district]
    
    parameter_values = {}
    for param_name, column_name in PARAMETER_MAPPING.items():
        if column_name in filtered_data.columns:
            values = filtered_data[column_name].dropna()
            if len(values) > 0:
                if values.dtype in ['float64', 'int64']:
                    parameter_values[param_name] = f"{values.mean():.2f}"
                else:
                    parameter_values[param_name] = str(values.mode().iloc[0]) if len(values.mode()) > 0 else "N/A"
            else:
                parameter_values[param_name] = "N/A"
        else:
            parameter_values[param_name] = "N/A"
    
    return parameter_values

# Find and load shapefile
shapefile_path = "Solar_Suitability_layer.shp"
for file in os.listdir('.'):
    if file.endswith('.shp'):
        shapefile_path = file
        break

gdf = load_shapefile(shapefile_path)

if gdf is not None:
    # Dashboard header
    st.markdown('<h1 class="dashboard-title">🌞 Solar Suitability Dashboard</h1>', unsafe_allow_html=True)
    
    # Top filters - clean and simple
    st.markdown('<div class="filter-section">', unsafe_allow_html=True)
    col1, col2, col3 = st.columns(3)
    
    with col1:
        st.markdown("**🌍 State**")
        states = ["All States"]
        if "NAME_1" in gdf.columns:
            valid_states = [str(s) for s in gdf["NAME_1"].unique() if s is not None and str(s) != "nan"]
            states.extend(sorted(valid_states))
        selected_state = st.selectbox("State", states, label_visibility="collapsed")
    
    with col2:
        st.markdown("**🏘️ District**")
        if selected_state != "All States":
            state_filtered = gdf[gdf["NAME_1"] == selected_state]
        else:
            state_filtered = gdf
            
        districts = ["All Districts"]
        if "NAME_2" in gdf.columns:
            valid_districts = [str(d) for d in state_filtered["NAME_2"].unique() if d is not None and str(d) != "nan"]
            districts.extend(sorted(valid_districts))
        selected_district = st.selectbox("District", districts, label_visibility="collapsed")
    
    with col3:
        st.markdown("**📊 Category**")
        selected_category = st.selectbox(
            "Category",
            list(categories.keys()),
            format_func=lambda x: categories[x],
            label_visibility="collapsed"
        )
    
    st.markdown('</div>', unsafe_allow_html=True)
    
    # Apply filters
    filtered_gdf = gdf.copy()
    if selected_state != "All States":
        filtered_gdf = filtered_gdf[filtered_gdf["NAME_1"] == selected_state]
    if selected_district != "All Districts":
        filtered_gdf = filtered_gdf[filtered_gdf["NAME_2"] == selected_district]
    
    # Main content - 3 columns layout
    map_col, stats_col, params_col = st.columns([2, 1, 1])
    
    # MAP COLUMN
    with map_col:
        st.markdown('<div class="section-header">🗺️ Solar Suitability Map</div>', unsafe_allow_html=True)
        
        if not filtered_gdf.empty:
            # Map bounds calculation
            if selected_state == "All States":
                try:
                    full_bounds = gdf.geometry.total_bounds
                    center_lat = (full_bounds[1] + full_bounds[3]) / 2
                    center_lon = (full_bounds[0] + full_bounds[2]) / 2
                    center = [center_lat, center_lon]
                    zoom_level = 4
                except:
                    center = [20.5937, 78.9629]
                    zoom_level = 4
            else:
                try:
                    bounds = filtered_gdf.geometry.total_bounds
                    center_lat = (bounds[1] + bounds[3]) / 2
                    center_lon = (bounds[0] + bounds[2]) / 2
                    center = [center_lat, center_lon]
                    
                    lat_diff = bounds[3] - bounds[1]
                    lon_diff = bounds[2] - bounds[0]
                    
                    if lat_diff > 8 or lon_diff > 8:
                        zoom_level = 6
                    elif lat_diff > 3 or lon_diff > 3:
                        zoom_level = 7
                    elif lat_diff > 1 or lon_diff > 1:
                        zoom_level = 8
                    else:
                        zoom_level = 9
                except:
                    center = [20.5937, 78.9629]
                    zoom_level = 5
            
            # Create map
            m = folium.Map(location=center, zoom_start=zoom_level, tiles="CartoDB dark_matter")
            
            # Fit bounds for full view
            if selected_state == "All States":
                try:
                    full_bounds = gdf.geometry.total_bounds
                    lat_padding = (full_bounds[3] - full_bounds[1]) * 0.05
                    lon_padding = (full_bounds[2] - full_bounds[0]) * 0.05
                    
                    southwest = [full_bounds[1] - lat_padding, full_bounds[0] - lon_padding]
                    northeast = [full_bounds[3] + lat_padding, full_bounds[2] + lon_padding]
                    
                    m.fit_bounds([southwest, northeast])
                except:
                    pass
            
            # Style function
            category_colors = get_category_colors(selected_category)
            
            def style_function(feature):
                if selected_category in feature['properties'] and feature['properties'][selected_category] is not None:
                    category_value = str(feature['properties'][selected_category])
                    
                    if category_value in category_colors:
                        color = category_colors[category_value]
                    else:
                        if "Highly Suitable" in category_value:
                            color = '#66BB6A'
                        elif "Moderately Suitable" in category_value:
                            color = '#FFEB3B'
                        elif "Less Suitable" in category_value:
                            color = '#F44336'
                        else:
                            color = '#BBBBBB'
                    
                    return {'fillColor': color, 'color': 'black', 'weight': 1, 'fillOpacity': 0.7}
                else:
                    return {'fillColor': '#BBBBBB', 'color': 'black', 'weight': 1, 'fillOpacity': 0.7}
            
            # Add data to map
            folium.GeoJson(filtered_gdf, style_function=style_function).add_to(m)
            
            # Display map
            folium_static(m, height=400)
        else:
            st.warning("No data available for selected filters.")
    
    # STATISTICS COLUMN
    with stats_col:
        st.markdown('<div class="section-header">📊 Summary Statistics</div>', unsafe_allow_html=True)
        
        stats = calculate_statistics(filtered_gdf, selected_category)
        
        if stats and 'counts' in stats:
            levels = list(stats['counts'].keys())
            percentages = [stats['counts'][level]['percentage'] for level in levels]
            total = sum([stats['counts'][level]['count'] for level in levels])
            
            # Show total
            st.markdown(f"""
            <div class="compact-metric">
                <span class="metric-name"><strong>Total Features</strong></span>
                <span class="metric-value">{total}</span>
            </div>
            """, unsafe_allow_html=True)
            
            # Show distribution
            category_colors = get_category_colors(selected_category)
            
            for level in levels:
                percentage = stats['counts'][level]['percentage']
                
                if level in category_colors:
                    color = category_colors[level]
                else:
                    if "Highly Suitable" in level:
                        color = "#66BB6A"
                    elif "Moderately Suitable" in level:
                        color = "#FFEB3B" 
                    elif "Less Suitable" in level:
                        color = "#F44336"
                    else:
                        color = "#BBBBBB"
                
                display_name = level[:25] + "..." if len(level) > 25 else level
                
                st.markdown(f"""
                <div class="compact-metric">
                    <span class="metric-name">
                        <span style="display: inline-block; width: 10px; height: 10px; background-color: {color}; margin-right: 6px; border-radius: 2px;"></span>
                        {display_name}
                    </span>
                    <span class="metric-value">{percentage:.1f}%</span>
                </div>
                """, unsafe_allow_html=True)
            
            # Compact pie chart
            if len(levels) <= 6:
                fig, ax = plt.subplots(figsize=(3.5, 3.5))
                
                pie_colors = []
                for level in levels:
                    if level in category_colors:
                        pie_colors.append(category_colors[level])
                    else:
                        if "Highly Suitable" in level:
                            pie_colors.append('#66BB6A')
                        elif "Moderately Suitable" in level:
                            pie_colors.append('#FFEB3B')
                        elif "Less Suitable" in level:
                            pie_colors.append('#F44336')
                        else:
                            pie_colors.append('#BBBBBB')
                
                wedges, texts, autotexts = ax.pie(
                    percentages, 
                    colors=pie_colors,
                    autopct='%1.1f%%',
                    startangle=90,
                    textprops={'fontsize': 8}
                )
                
                fig.patch.set_facecolor('#2C3E50')
                ax.set_facecolor('#2C3E50')
                
                for autotext in autotexts:
                    autotext.set_color('white')
                    autotext.set_fontweight('bold')
                    autotext.set_fontsize(8)
                
                for text in texts:
                    text.set_fontsize(0)  # Hide labels to save space
                
                plt.tight_layout()
                st.pyplot(fig)
                plt.close()
        else:
            st.markdown('<div class="compact-metric"><span class="metric-name">No statistics available</span></div>', unsafe_allow_html=True)
    
    # PARAMETERS COLUMN  
    with params_col:
        st.markdown('<div class="section-header">📋 Key Parameters</div>', unsafe_allow_html=True)
        
        parameter_values = get_parameter_values(filtered_gdf, selected_state, selected_district)
        
        for param_name, value in parameter_values.items():
            # Get icon
            if "Solar" in param_name or "Aridity" in param_name:
                icon = "☀️"
            elif "Water" in param_name or "Irrigation" in param_name:
                icon = "💧"
            elif "Land" in param_name or "Area" in param_name:
                icon = "🌾"
            elif "Energy" in param_name or "Electric" in param_name:
                icon = "⚡"
            elif "Farmers" in param_name or "Holdings" in param_name:
                icon = "👨‍🌾"
            else:
                icon = "📊"
            
            st.markdown(f"""
            <div class="compact-metric">
                <span class="metric-name">{icon} {param_name}</span>
                <span class="metric-value">{value}</span>
            </div>
            """, unsafe_allow_html=True)

else:
    st.error("Could not load shapefile. Please check file availability.")