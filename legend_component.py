import streamlit as st

def get_category_colors(category):
    """
    Returns the color mapping for map styling based on category
    """
    color_mappings = {
        "Adaptation": {
            "Less Suitable": "#F44336",          # Red
            "Moderately Suitable": "#FFEB3B",   # Yellow
            "Highly Suitable": "#2007FF",       # Changed to amber/yellowish
            "Very Highly Suitable": "#2E7D32",  # Dark green
        },
        
        "Mitigation": {
            "Less Suitable": "#D32F2F",          # Dark red
            "Moderately Suitable": "#FFEB3B",   # Yellow
            "Highly Suitable": "#FFC107",       # Changed to amber/yellowish
            "Very High Suitable": "#2E7D32",    # Dark green
        },
        
        "Replacment": {
            "Less Suitable": "#8D6E63",                                   # Brown
            "Moderately Suitable": "#FFEB3B",                           # Yellow
            "Highly Suitable": "#FFB007",                                # Changed to amber/yellowish
            "Highly Suitable (On Grid)": "#66BB6A",                      # Light green
            "Highly Suitable (Community Wells)": "#4CAF50",              # Medium green
            "Highly Suitable (On Grid Community Wells)": "#2E7D32",      # Dark green
        },
        
        "General_SI": {
            "Less Suitable": "#F44336",                                                    # Red
            "Moderately Suitable": "#FFEB3B",                                             # Yellow
            "Highly Suitable (On Grid Replacement)": "#A5D6A7",                           # Very light green
            "Highly Suitable (On Grid Community Wells)": "#66BB6A",                       # Light green
            "Highly Suitable (Mitigation + On Grid Replacement)": "#26A69A",              # Medium teal
            "Highly Suitable (Mitigation + On Grid Community We": "#00695C",              # Dark teal
            "Highly Suitable (Mitigation)": "#4DB6AC",                                     # Teal
            "Highly Suitable (Adaptation + On Grid Replacement)": "#B39DDB",              # Light purple
            "Highly Suitable (Adaptation + On Grid Community We": "#81D4FA",              # Light blue
            "Highly Suitable (Adaptation + Mitigation + On Grid": "#1976D2",              # Dark blue
            "Highly Suitable (Adaptation + Mitigation)": "#2196F3",                       # Blue
            "Highly Suitable (Adaptation )": "#9C27B0",                                    # Purple
            "Highly Suitable": "#FFC107",                                                  # Changed to amber/yellowish (fallback)
        }
    }
    
    return color_mappings.get(category, {})