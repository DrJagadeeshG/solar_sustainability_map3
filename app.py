import streamlit as st
import pandas as pd
import geopandas as gpd
import folium
from streamlit_folium import st_folium
from streamlit_folium import folium_static
import os
import matplotlib.pyplot as plt
import numpy as np

# Helper for formatting values with units
def format_value_with_unit(value, unit):
    if pd.notna(value) and str(value) not in ['XX', 'N/A', 'nan', '']:
        try:
            if isinstance(value, (int, float)):
                return f"{value:.1f} {unit}".strip()
            else:
                return f"{value} {unit}".strip()
        except:
            return str(value)
    else:
        return "XX"

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

# Add professional styling
st.markdown("""
<style>
    /* Base styles */
    .main > div {
        padding: 1rem 2rem;
        background-color: #0E1117;
        color: #FAFAFA;
    }
    
    /* Dashboard title */
    .dashboard-title {
        font-size: 2.2rem;
        color: #00ADB5;
        text-align: center;
        margin-bottom: 2rem;
        font-weight: bold;
        padding: 1rem;
        border-bottom: 2px solid #00ADB5;
    }
    
    /* Filter section */
    .filter-section {
        background-color: #1A1B1E;
        padding: 1.5rem;
        border-radius: 10px;
        margin-bottom: 2rem;
        box-shadow: 0 4px 6px rgba(0,0,0,0.3);
        border: 1px solid #2C2E33;
    }
    
    /* Section headers */
    .section-header {
        color: #00ADB5;
        font-size: 1.2rem;
        font-weight: bold;
        margin-bottom: 0.5rem;
        padding-bottom: 0.5rem;
        border-bottom: 2px solid #00ADB5;
    }
    
    /* Map container */
    .map-container {
        background-color: transparent;
        padding: 0;
        margin: 0.5rem 0;
    }
    
    /* Status boxes */
    .status-box {
        padding: 0.8rem;
        border-radius: 6px;
        margin-bottom: 0.5rem;
        text-align: center;
        color: white;
    }
    
    .status-box.high {
        background-color: #00ADB5;
    }
    
    .status-box.medium {
        background-color: #F9B872;
    }
    
    .status-box.low {
        background-color: #FF6B6B;
    }
    
    /* Metric containers */
    .metric-container {
        background-color: #1A1B1E;
        padding: 0.8rem;
        border-radius: 8px;
        margin-bottom: 0.5rem;
        box-shadow: 0 2px 4px rgba(0,0,0,0.2);
        border: 1px solid #2C2E33;
    }
    
    /* Metric styling */
    .metric-name {
        color: #EEEEEE;
        font-size: 0.9rem;
        font-weight: 500;
    }
    
    .metric-value {
        color: #00ADB5;
        font-weight: bold;
        font-size: 0.9rem;
        float: right;
    }
    
    /* Text boxes */
    .text-box {
        background-color: #1A1B1E;
        padding: 1rem;
        border-radius: 8px;
        margin-bottom: 1rem;
        border-left: 4px solid #00ADB5;
        color: #EEEEEE;
    }
    
    /* Select box styling */
    .stSelectbox label {
        color: #EEEEEE !important;
        font-weight: bold;
    }
    
    /* Tooltip styling */
    .tooltip {
        position: relative;
        display: inline-block;
        cursor: help;
    }
    
    .tooltip .tooltiptext {
        visibility: hidden;
        width: 200px;
        background-color: #2C2E33;
        color: #EEEEEE;
        text-align: center;
        border-radius: 6px;
        padding: 8px;
        position: absolute;
        z-index: 1;
        bottom: 125%;
        left: 50%;
        margin-left: -100px;
        opacity: 0;
        transition: opacity 0.3s;
        font-size: 12px;
        border: 1px solid #00ADB5;
    }
    
    .tooltip:hover .tooltiptext {
        visibility: visible;
        opacity: 1;
    }
    
    /* Hide unnecessary elements */
    #MainMenu {visibility: hidden;}
    footer {visibility: hidden;}
    .stDeployButton {visibility: hidden;}
    
    /* Remove empty space around map */
    .stMarkdown {
        margin: 0;
        padding: 0;
    }
    
    /* Adjust folium map container */
    .folium-map {
        margin: 0 !important;
        padding: 0 !important;
    }
    
    iframe {
        margin: 0 !important;
        padding: 0 !important;
        border: none !important;
    }
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

# Updated Parameter mapping to match exact shapefile columns
PARAMETER_MAPPING = {
    "Solar Radiance": "Solar_Rad",
    "Cropping Intensity (%)": "Crop_Inten", 
    "Irrigation Coverage (%)": "Irrig_Inte",
    "Irrigation Water Requirement": "IWU",
    "Cultivated Land (% of total)": "Cult_land",
    "Pump Energy Source (Electric)": "Elect(%)",
    "Energy Subsidy": "Elec_Sub",
    "Groundwater Development (%)": "GW_Dev",
    "Aquifer Depth (mbgl)": "GWL (m)",
    "Surface Water Body (ha)": "SW_Body",
    "Small & Marginal Holdings (%)": "S_M Holdin",
    "Farmers Average Area (ha)": "Avg Area p",
    "Land Fragmentation": "Avg. No. o",
    "Number of Pumps": "No of pump"
}

# Objective tooltips
OBJECTIVE_TOOLTIPS = {
    "Adapt": "Focuses on helping farmers adapt to climate change impacts through solar solutions for irrigation and crop management.",
    "Mitigate": "Aims to reduce greenhouse gas emissions by replacing fossil fuel-based energy systems with solar alternatives.",
    "Replace": "Involves replacing existing conventional energy sources with solar power systems for agricultural operations.",
    "General_SI": "General Solar Initiative - comprehensive assessment covering multiple solar suitability factors for diverse applications."
}

categories = {
    "Adapt": "Adaptation",
    "Mitigate": "Mitigation", 
    "Replace": "Replacement",
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

def get_district_details(gdf, state_name, district_name):
    """
    Get detailed information for a specific district with better matching
    """
    if state_name == "All States" or district_name == "All Districts":
        return None
    
    # Try exact match first
    district_data = gdf[
        (gdf["NAME_1"] == state_name) & 
        (gdf["NAME_2"] == district_name)
    ]
    
    # If no exact match, try case-insensitive match
    if len(district_data) == 0:
        district_data = gdf[
            (gdf["NAME_1"].str.lower() == state_name.lower()) & 
            (gdf["NAME_2"].str.lower() == district_name.lower())
        ]
    
    # If still no match, try partial match
    if len(district_data) == 0:
        district_data = gdf[
            (gdf["NAME_1"].str.contains(state_name, case=False, na=False)) & 
            (gdf["NAME_2"].str.contains(district_name, case=False, na=False))
        ]
    
    if len(district_data) == 0:
        st.warning(f"No data found for {district_name}, {state_name}")
        return None
    
    return district_data.iloc[0]

def render_district_dashboard(district_data, selected_category):
    """
    Render detailed district-level dashboard with all categories side by side
    """
    # Create layout with all sections side by side
    col1, col2, col3, col4, col5, col6 = st.columns(6)
    
    # COLUMN 1: District Information
    with col1:
        st.markdown('<div class="section-header">District</div>', unsafe_allow_html=True)
        
        # Map first with no padding
        gdf = st.session_state.get('gdf', None)
        if gdf is not None:
            district_name = district_data.get('NAME_2', 'Unknown District')
            state_name = district_data.get('NAME_1', 'Unknown State')
            district_gdf = gdf[(gdf['NAME_1'] == state_name) & (gdf['NAME_2'] == district_name)]
            if not district_gdf.empty:
                district_gdf_web = district_gdf.to_crs(epsg=3857)
                district_gdf_wgs = district_gdf_web.to_crs(epsg=4326)
                centroid_wgs = district_gdf_wgs.geometry.centroid.iloc[0]
                
                m = folium.Map(
                    location=[centroid_wgs.y, centroid_wgs.x],
                    zoom_start=8,
                    tiles="CartoDB dark_matter",
                    width='100%',
                    height='250px'
                )
                
                folium.GeoJson(
                    district_gdf_wgs,
                    style_function=lambda x: {
                        'fillColor': '#00ADB5',
                        'color': '#00ADB5',
                        'weight': 2,
                        'fillOpacity': 0.3
                    }
                ).add_to(m)
                
                m.fit_bounds([[district_gdf_wgs.geometry.bounds.miny.iloc[0], 
                             district_gdf_wgs.geometry.bounds.minx.iloc[0]],
                            [district_gdf_wgs.geometry.bounds.maxy.iloc[0], 
                             district_gdf_wgs.geometry.bounds.maxx.iloc[0]]])
                
                st_folium(m, height=250, width=None)
            else:
                st.info("District geometry not found")
        else:
            st.info("Map data not loaded")
        
        # Status boxes second
        for objective, label in [
            ('Adapt', 'Adaptation'),
            ('Mitigate', 'Mitigation'),
            ('Replace', 'Sustainability')
        ]:
            status = district_data.get(objective, 'Medium')
            status_class = 'high' if status in ['High', 'Very High'] else 'low' if status == 'Low' else 'medium'
            st.markdown(f"""
            <div class="status-box {status_class}">
                <div style="font-size: 0.8rem;">{label}: {status}</div>
            </div>
            """, unsafe_allow_html=True)
        
        # District and state info last
        st.markdown(f"""
        <div class="metric-container">
            <span class="metric-name">District</span>
            <span class="metric-value">{district_name}</span>
        </div>
        <div class="metric-container">
            <span class="metric-name">State</span>
            <span class="metric-value">{state_name}</span>
        </div>
        """, unsafe_allow_html=True)
    
    # COLUMN 2: Crop Information
    with col2:
        st.markdown('<div class="section-header">Crop</div>', unsafe_allow_html=True)
        crop_params = [
            ("Crop_Inten", "Cropping intensity", "%"),
            ("Cult_land", "Cultivated land", "%")
        ]
        for param_col, param_name, unit in crop_params:
            value = district_data.get(param_col, 'XX')
            display_value = format_value_with_unit(value, unit)
            st.markdown(f"""
            <div class="metric-container">
                <span class="metric-name">{param_name}</span>
                <span class="metric-value">{display_value}</span>
            </div>
            """, unsafe_allow_html=True)
        
        crop_text = district_data.get('Text-Crop', '')
        if pd.notna(crop_text) and str(crop_text).strip() and str(crop_text) != 'N/A':
            st.markdown(f"""
            <div class="text-box">
                <div style="font-size: 0.8rem;">{crop_text}</div>
            </div>
            """, unsafe_allow_html=True)
    
    # COLUMN 3: Water Information
    with col3:
        st.markdown('<div class="section-header">Water</div>', unsafe_allow_html=True)
        water_params = [
            ("Irrig_Inte", "Irrigation coverage", "%"),
            ("GW_Dev", "GW development", "%"),
            ("SW_Body", "SW bodies area", "ha")
        ]
        for param_col, param_name, unit in water_params:
            value = district_data.get(param_col, 'XX')
            display_value = format_value_with_unit(value, unit)
            st.markdown(f"""
            <div class="metric-container">
                <span class="metric-name">{param_name}</span>
                <span class="metric-value">{display_value}</span>
            </div>
            """, unsafe_allow_html=True)
        
        water_text = district_data.get('Text-Water', '')
        if pd.notna(water_text) and str(water_text).strip() and str(water_text) != 'N/A':
            st.markdown(f"""
            <div class="text-box">
                <div style="font-size: 0.8rem;">{water_text}</div>
            </div>
            """, unsafe_allow_html=True)
    
    # COLUMN 4: Energy Information
    with col4:
        st.markdown('<div class="section-header">Energy</div>', unsafe_allow_html=True)
        energy_params = [
            ("Elect(%)", "Electric pumps", "%"),
            ("Diesel (%)", "Diesel pumps", "%"),
            ("No of pump", "Total pumps", ""),
            ("Emission (", "Emissions", "kg CO2")
        ]
        for param_col, param_name, unit in energy_params:
            value = district_data.get(param_col, 'XX')
            display_value = format_value_with_unit(value, unit)
            st.markdown(f"""
            <div class="metric-container">
                <span class="metric-name">{param_name}</span>
                <span class="metric-value">{display_value}</span>
            </div>
            """, unsafe_allow_html=True)
    
    # COLUMN 5: Utility Information
    with col5:
        st.markdown('<div class="section-header">Utility</div>', unsafe_allow_html=True)
        utility_params = [
            ("DISCOM Nam", "DISCOM", ""),
            ("DISCOM Rat", "DISCOM health", ""),
            ("Elec_Sub", "Subsidy", "")
        ]
        for param_col, param_name, unit in utility_params:
            value = district_data.get(param_col, 'N/A')
            display_value = str(value) if pd.notna(value) and str(value) not in ['N/A', 'nan', ''] else 'N/A'
            st.markdown(f"""
            <div class="metric-container">
                <span class="metric-name">{param_name}</span>
                <span class="metric-value">{display_value}</span>
            </div>
            """, unsafe_allow_html=True)
        
        utility_text = district_data.get('Text-Utilt', '')
        if pd.notna(utility_text) and str(utility_text).strip() and str(utility_text) != 'N/A':
            st.markdown(f"""
            <div class="text-box">
                <div style="font-size: 0.8rem;">{utility_text}</div>
            </div>
            """, unsafe_allow_html=True)
    
    # COLUMN 6: Farmer Information
    with col6:
        st.markdown('<div class="section-header">Farmer</div>', unsafe_allow_html=True)
        farmer_params = [
            ("S_M Holdin", "Small & Marginal", "%"),
            ("Avg Area p", "Average area", "ha"),
            ("Avg. No. o", "Number of parcels", "")
        ]
        for param_col, param_name, unit in farmer_params:
            value = district_data.get(param_col, 'XX')
            display_value = format_value_with_unit(value, unit)
            st.markdown(f"""
            <div class="metric-container">
                <span class="metric-name">{param_name}</span>
                <span class="metric-value">{display_value}</span>
            </div>
            """, unsafe_allow_html=True)
        
        farmer_text = district_data.get('Text-Farme', '')
        if pd.notna(farmer_text) and str(farmer_text).strip() and str(farmer_text) != 'N/A':
            st.markdown(f"""
            <div class="text-box">
                <div style="font-size: 0.8rem;">{farmer_text}</div>
            </div>
            """, unsafe_allow_html=True)

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

def render_national_state_dashboard(filtered_gdf, selected_category, selected_state):
    """
    Render the original national/state level dashboard
    """
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
                        if "Less Suitable" in category_value:
                            color = '#FF6B6B'  # Coral Red
                        elif "Moderately Suitable" in category_value:
                            color = '#845EC2'  # Purple
                        elif "Highly Suitable" in category_value:
                            color = '#00ADB5'  # Cyan/Turquoise
                        elif "Very Highly Suitable" in category_value:
                            color = '#2ECC71'  # Emerald Green
                        else:
                            color = '#2C2E33'  # Dark Gray
                    
                    return {'fillColor': color, 'color': 'black', 'weight': 1, 'fillOpacity': 0.7}
                else:
                    return {'fillColor': '#2C2E33', 'color': 'black', 'weight': 1, 'fillOpacity': 0.7}
            
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
            
            # Show distribution
            category_colors = get_category_colors(selected_category)
            
            for level in levels:
                percentage = stats['counts'][level]['percentage']
                
                if level in category_colors:
                    color = category_colors[level]
                else:
                    if "Less Suitable" in level:
                        color = '#FF6B6B'  # Coral Red
                    elif "Moderately Suitable" in level:
                        color = '#845EC2'  # Purple
                    elif "Highly Suitable" in level:
                        color = '#00ADB5'  # Cyan/Turquoise
                    elif "Very Highly Suitable" in level:
                        color = '#2ECC71'  # Emerald Green
                    else:
                        color = '#2C2E33'  # Dark Gray
                
                display_name = level[:25] + "..." if len(level) > 25 else level
                
                st.markdown(f"""
                <div class="metric-container">
                    <span class="metric-name">
                        <span style="display: inline-block; width: 10px; height: 10px; background-color: {color}; margin-right: 6px; border-radius: 2px;"></span>
                        {display_name}
                    </span>
                    <span class="metric-value">{percentage:.1f}%</span>
                </div>
                """, unsafe_allow_html=True)
            
            # Compact pie chart
            if len(levels) <= 6:
                try:
                    fig, ax = plt.subplots(figsize=(3.5, 3.5))
                    pie_colors = []
                    for level in levels:
                        if level in category_colors:
                            pie_colors.append(category_colors[level])
                        else:
                            if "Less Suitable" in level:
                                pie_colors.append('#FF6B6B')  # Coral Red
                            elif "Moderately Suitable" in level:
                                pie_colors.append('#845EC2')  # Purple
                            elif "Highly Suitable" in level:
                                pie_colors.append('#00ADB5')  # Cyan/Turquoise
                            elif "Very Highly Suitable" in level:
                                pie_colors.append('#2ECC71')  # Emerald Green
                            else:
                                pie_colors.append('#2C2E33')  # Dark Gray
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
                except Exception as chart_error:
                    st.write("Chart could not be rendered")
        else:
            st.markdown('<div class="metric-container"><span class="metric-name">No statistics available</span></div>', unsafe_allow_html=True)
    
    # PARAMETERS COLUMN  
    with params_col:
        st.markdown('<div class="section-header">📋 Key Parameters</div>', unsafe_allow_html=True)
        parameter_values = get_parameter_values(filtered_gdf, selected_state, "All Districts")
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
            <div class="metric-container">
                <span class="metric-name">{icon} {param_name}</span>
                <span class="metric-value">{value}</span>
            </div>
            """, unsafe_allow_html=True)

# Main app logic
shapefile_path = None
if os.path.exists("true_solar_suitability.shp"):
    shapefile_path = "true_solar_suitability.shp"
elif os.path.exists("Solar_Suitability_layer.shp"):
    shapefile_path = "Solar_Suitability_layer.shp"
else:
    # Fallback to any .shp file
    for file in os.listdir('.'):
        if file.endswith('.shp'):
            shapefile_path = file
            break

gdf = load_shapefile(shapefile_path)

if gdf is not None:
    # Store GeoDataFrame in session state for use in district view
    st.session_state['gdf'] = gdf
    
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
        st.markdown("**🎯 Objective**")
        objective_options = list(categories.keys())
        selected_category = st.selectbox(
            "Objective",
            objective_options,
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
    
    # Check if showing district-level detail
    show_district_dashboard = (selected_state != "All States" and selected_district != "All Districts")
    
    if show_district_dashboard:
        # Show detailed district dashboard
        district_data = get_district_details(gdf, selected_state, selected_district)
        if district_data is not None:
            render_district_dashboard(district_data, selected_category)
        else:
            st.error("District data not found")
    else:
        # Show original national/state level dashboard
        render_national_state_dashboard(filtered_gdf, selected_category, selected_state)
else:
    st.error("Could not load shapefile. Please check file availability.")