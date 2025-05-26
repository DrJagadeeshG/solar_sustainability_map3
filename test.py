import geopandas as gpd
gdf = gpd.read_file("true_solar_suitability.shp")
print("Available columns in shapefile:")
for i, col in enumerate(gdf.columns):
    print(f"{i+1}. {col}")