# Solar Suitability Dashboard

An interactive Streamlit dashboard for visualizing and analyzing solar suitability across different regions. The dashboard provides detailed insights into various parameters affecting solar implementation potential.

## Features

- Interactive map visualization with district-level data
- Multi-parameter analysis including:
  - Crop information
  - Water resources
  - Energy usage
  - Utility details
  - Farmer demographics
- Customizable filters for state and district selection
- Detailed statistics and parameter breakdowns
- Professional dark theme UI

## Installation

1. Clone the repository:
```bash
git clone https://github.com/DrJagadeeshG/solar_sustainability_map4.git
cd solar_sustainability_map4
```

2. Install dependencies:
```bash
pip install -r requirements.txt
```

3. Run the application:
```bash
streamlit run app.py
```

## Data Requirements

The application expects a shapefile with the following data:
- District boundaries
- Solar suitability parameters
- Agricultural data
- Water resource information
- Energy usage statistics
- Utility information
- Farmer demographics

Place your shapefile in the root directory with one of these names:
- true_solar_suitability.shp
- Solar_Suitability_layer.shp

## License

This project is licensed under the MIT License. 