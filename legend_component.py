import streamlit as st

def get_category_colors(category):
    """
    Returns the color mapping for map styling based on category
    """
    color_mappings = {
        "Adaptation": {
            "Less Suitable": "#FF1E1E",          # Bright Red
            "Moderately Suitable": "#FFB300",    # Amber
            "Highly Suitable": "#7B1FA2",        # Deep Purple
            "Very Highly Suitable": "#1E88E5",   # Blue
        },
        
        "Mitigation": {
            "Less Suitable": "#D81B60",          # Pink
            "Moderately Suitable": "#FFC107",    # Yellow
            "Highly Suitable": "#004D40",        # Teal
            "Very High Suitable": "#76FF03",     # Light Green
        },
        
        "Replacment": {
            "Less Suitable": "#C51162",                                   # Pink
            "Moderately Suitable": "#AA00FF",                            # Purple
            "Highly Suitable": "#00C853",                                # Green
            "Highly Suitable (On Grid)": "#FF3D00",                      # Deep Orange
            "Highly Suitable (Community Wells)": "#2962FF",              # Blue
            "Highly Suitable (On Grid Community Wells)": "#FFD600",      # Yellow
        },
        
        "General_SI": {
            "Less Suitable": "#FF4081",                                                    # Pink A200
            "Moderately Suitable": "#B388FF",                                             # Deep Purple A100
            "Highly Suitable (On Grid Replacement)": "#FF6E40",                           # Deep Orange A200
            "Highly Suitable (On Grid Community Wells)": "#69F0AE",                       # Green A200
            "Highly Suitable (Mitigation + On Grid Replacement)": "#40C4FF",              # Light Blue A200
            "Highly Suitable (Mitigation + On Grid Community Wells)": "#FFAB40",          # Orange A200
            "Highly Suitable (Mitigation)": "#EA80FC",                                    # Purple A100
            "Highly Suitable (Adaptation + On Grid Replacement)": "#FF9E80",              # Deep Orange A100
            "Highly Suitable (Adaptation + On Grid Community Wells)": "#B9F6CA",          # Green A100
            "Highly Suitable (Adaptation + Mitigation + On Grid)": "#84FFFF",             # Cyan A200
            "Highly Suitable (Adaptation + Mitigation + On Grid Community Wells)": "#FFE57F", # Yellow A100
            "Highly Suitable (Adaptation + Mitigation)": "#FF80AB",                       # Pink A100
            "Highly Suitable (Adaptation)": "#8C9EFF",                                    # Indigo A100
            "Highly Suitable": "#F4511E",                                                 # Deep Orange 600
            "Very Highly Suitable": "#00BFA5",                                            # Teal A700
            "Highly Suitable (Community Wells)": "#7C4DFF",                               # Deep Purple A200
            "Highly Suitable (On Grid + Community Wells)": "#FF6D00",                     # Orange A700
            "Highly Suitable (Adaptation + Community Wells)": "#64DD17",                  # Light Green A700
            "Highly Suitable (Mitigation + Community Wells)": "#00B8D4",                  # Cyan A700
            "Highly Suitable (Adaptation + Mitigation + Community Wells)": "#AEEA00",     # Lime A700
        }
    }
    
    return color_mappings.get(category, {})