import pandas as pd
import geopandas as gpd
import os
from pathlib import Path
import numpy as np

def create_true_solar_suitability_shapefile():
    """
    Creates a new shapefile with actual solar suitability data from Excel workbook
    """
    
    print("=== Creating True Solar Suitability Shapefile ===")
    
    # 1. Load the original shapefile
    print("1. Loading original shapefile...")
    try:
        if os.path.exists("Solar_Suitability_layer.shp"):
            gdf = gpd.read_file("Solar_Suitability_layer.shp")
            print(f"   ✅ Loaded shapefile with {len(gdf)} features")
            print(f"   Original columns: {list(gdf.columns)}")
        else:
            print("   ❌ Solar_Suitability_layer.shp not found!")
            return False
    except Exception as e:
        print(f"   ❌ Error loading shapefile: {e}")
        return False
    
    # 1.5. CLEAN OUT DUMMY DATA - Keep only essential geographic columns
    print("\n1.5. Removing dummy/placeholder data from original shapefile...")
    
    # Keep only NAME columns and geometry (remove all BS data)
    essential_geographic_cols = ['geometry']
    
    # Keep NAME columns (administrative boundaries)
    name_columns = []
    for col in gdf.columns:
        if col.upper().startswith('NAME_') or col.upper() == 'NAME':
            name_columns.append(col)
            essential_geographic_cols.append(col)
    
    print(f"   Keeping essential columns: {essential_geographic_cols}")
    print(f"   Removing BS columns: {[col for col in gdf.columns if col not in essential_geographic_cols]}")
    
    # Create clean GeoDataFrame with only geographic essentials
    clean_gdf = gdf[essential_geographic_cols].copy()
    
    print(f"   ✅ Cleaned shapefile: {len(clean_gdf)} features, {len(clean_gdf.columns)} columns")
    print(f"   Clean columns: {list(clean_gdf.columns)}")
    
    # Update gdf to use the cleaned version
    gdf = clean_gdf
    
    # 2. Load Excel workbook
    print("\n2. Loading Excel workbook...")
    try:
        excel_file = "Solar_Suitability_workbook.xlsx"
        
        # Load key sheets
        solar_ranking = pd.read_excel(excel_file, sheet_name="Solar Suitability_new_ranking")
        district_recommendations = pd.read_excel(excel_file, sheet_name="District_recommendation")
        adaptation_data = pd.read_excel(excel_file, sheet_name="Adaptation")
        mitigation_data = pd.read_excel(excel_file, sheet_name="Mitigation")
        replacement_data = pd.read_excel(excel_file, sheet_name="Replacement")
        community_sip = pd.read_excel(excel_file, sheet_name="Community SIP")
        gis_acronym = pd.read_excel(excel_file, sheet_name="GIS layer accronym")
        potential_data = pd.read_excel(excel_file, sheet_name="potential")
        all_data = pd.read_excel(excel_file, sheet_name="All")
        
        print(f"   ✅ Loaded Excel data:")
        print(f"      - Solar ranking: {len(solar_ranking)} records")
        print(f"      - District recommendations: {len(district_recommendations)} records, {len(district_recommendations.columns)} columns")
        print(f"      - GIS acronym mapping: {len(gis_acronym)} mappings")
        print(f"      - Community SIP: {len(community_sip)} records")
        print(f"      - Potential data: {len(potential_data)} records")
        
        # Show district recommendation columns
        print(f"      - District recommendation columns: {list(district_recommendations.columns)}")
        
    except Exception as e:
        print(f"   ❌ Error loading Excel file: {e}")
        return False
    
    # 3. Prepare data for merging
    print("\n3. Preparing data for merging...")
    
    # 3.1 Create GIS acronym mapping dictionary
    print("   3.1 Processing GIS acronym mappings...")
    acronym_mapping = {}
    
    for _, row in gis_acronym.iterrows():
        original_name = row['Original']
        gis_raw_name = row['GIS Raw data layer']
        if pd.notna(original_name) and pd.notna(gis_raw_name):
            acronym_mapping[original_name] = gis_raw_name
    
    print(f"      ✅ Created {len(acronym_mapping)} acronym mappings")
    for orig, gis_name in list(acronym_mapping.items())[:5]:  # Show first 5
        print(f"         {orig} → {gis_name}")
    
    # 3.2 Process District Recommendations with proper column naming
    print("   3.2 Processing District Recommendations...")
    
    district_rec_processed = district_recommendations.copy()
    
    # Create mapping for district recommendation columns
    district_rec_column_mapping = {}
    
    for col in district_rec_processed.columns:
        if col in ['State', 'District']:  # Keep key columns as is
            new_col_name = col
        elif col in acronym_mapping:
            # Use GIS acronym mapping
            new_col_name = acronym_mapping[col]
            print(f"      Mapped: {col} → {new_col_name}")
        else:
            # Use first 10 characters if no acronym mapping found
            new_col_name = col[:10]
            if len(col) > 10:
                print(f"      Truncated: {col} → {new_col_name}")
        
        district_rec_column_mapping[col] = new_col_name
    
    # Apply column mapping to district recommendations
    district_rec_processed = district_rec_processed.rename(columns=district_rec_column_mapping)
    
    print(f"      ✅ District recommendations processed: {len(district_rec_processed.columns)} columns")
    print(f"      New column names: {list(district_rec_processed.columns)}")
    
    # 3.3 Create master data from solar ranking as base
    master_data = solar_ranking.copy()
    master_data.columns = ['District', 'Adaptation_New', 'Mitigation_New', 'Replacement_New']
    
    # 3.4 Merge with processed district recommendations
    print("   3.3 Merging solar ranking with district recommendations...")
    
    # Standardize district names for matching
    master_data['District_Clean'] = master_data['District'].str.title().str.strip()
    district_rec_processed['District_Clean'] = district_rec_processed['District'].str.title().str.strip()
    
    # Merge district recommendations
    master_data = master_data.merge(
        district_rec_processed, 
        on='District_Clean', 
        how='left',
        suffixes=('', '_district_rec')
    )
    
    # Remove duplicate District columns if any
    duplicate_cols = [col for col in master_data.columns if col.endswith('_district_rec') and col.replace('_district_rec', '') in master_data.columns]
    if duplicate_cols:
        master_data = master_data.drop(columns=duplicate_cols)
    
    print(f"      ✅ Merged data: {len(master_data)} records, {len(master_data.columns)} columns")
    
    # 3.5 Add Community SIP information
    print("   3.4 Adding Community SIP information...")
    community_sip_clean = community_sip[['State', 'District', 'Final']].copy()
    community_sip_clean['State'] = community_sip_clean['State'].str.title()
    community_sip_clean['District_Clean'] = community_sip_clean['District'].str.title().str.strip()
    community_sip_clean = community_sip_clean.rename(columns={'Final': 'Community_SIP'})
    
    master_data = master_data.merge(
        community_sip_clean[['District_Clean', 'Community_SIP']],
        on='District_Clean',
        how='left'
    )
    
    # Fill NaN Community SIP with empty string
    master_data['Community_SIP'] = master_data['Community_SIP'].fillna('')
    
    # 3.6 Add comprehensive potential data
    print("   3.5 Adding potential data...")
    potential_clean = potential_data[['District', 'Final Potential']].copy()
    potential_clean['District_Clean'] = potential_clean['District'].str.title().str.strip()
    potential_clean = potential_clean.rename(columns={'Final Potential': 'Overall_Potential'})
    
    master_data = master_data.merge(
        potential_clean[['District_Clean', 'Overall_Potential']],
        on='District_Clean',
        how='left'
    )
    
    print(f"   ✅ Master data prepared with {len(master_data)} records, {len(master_data.columns)} columns")
    print(f"   Final master data columns: {list(master_data.columns)}")
    
    # 4. Match and merge with shapefile
    print("\n4. Matching with shapefile...")
    
    # Create matching keys - try different combinations
    def create_match_key(name):
        if pd.isna(name):
            return ""
        return str(name).lower().strip().replace(' ', '').replace('-', '').replace('.', '')
    
    # Add matching keys to both datasets
    master_data['match_key'] = master_data['District_Clean'].apply(create_match_key)
    
    # Try matching with NAME_2 column from shapefile
    if 'NAME_2' in gdf.columns:
        gdf['match_key'] = gdf['NAME_2'].apply(create_match_key)
        match_column = 'NAME_2'
    elif 'District' in gdf.columns:
        gdf['match_key'] = gdf['District'].apply(create_match_key)
        match_column = 'District'
    else:
        print("   ❌ No suitable district column found in shapefile")
        return False
    
    print(f"   Using {match_column} column for matching")
    
    # Perform the merge
    merged_gdf = gdf.merge(
        master_data,
        on='match_key',
        how='left'
    )
    
    # Check merge success
    successful_merges = merged_gdf['Adaptation_New'].notna().sum()
    print(f"   ✅ Successfully matched {successful_merges}/{len(gdf)} features")
    
    if successful_merges == 0:
        print("   ⚠️  Warning: No successful matches found!")
        print("   Sample shapefile districts:", gdf[match_column].head().tolist())
        print("   Sample Excel districts:", master_data['District'].head().tolist())
    
    # 5. Clean up and finalize columns
    print("\n5. Finalizing new shapefile...")
    
    # Remove temporary matching column and duplicates
    merged_gdf = merged_gdf.drop('match_key', axis=1)
    merged_gdf = merged_gdf.drop('District_Clean', axis=1, errors='ignore')
    
    # Remove duplicate columns (keep first occurrence)
    merged_gdf = merged_gdf.loc[:, ~merged_gdf.columns.duplicated()]
    
    # Start with essential columns
    essential_cols = ['geometry']  # Always keep geometry
    
    # Add the NAME columns we kept from original shapefile
    for col in gdf.columns:
        if col != 'geometry' and col not in ['match_key']:
            essential_cols.append(col)
    
    # Create shapefile-friendly names for core suitability data
    core_suitability_mapping = {
        'Adaptation_New': 'Adapt',
        'Mitigation_New': 'Mitigate', 
        'Replacement_New': 'Replace',
        'Overall_Potential': 'General_SI',
        'Community_SIP': 'Comm_SIP',
        'State': 'State_Name',
        'District': 'Dist_Name'
    }
    
    # Apply core mapping and add to essential columns
    for old_name, new_name in core_suitability_mapping.items():
        if old_name in merged_gdf.columns:
            merged_gdf[new_name] = merged_gdf[old_name]
            essential_cols.append(new_name)
    
    # Create Community SIP boolean (shapefile friendly name)
    if 'Comm_SIP' in merged_gdf.columns:
        merged_gdf['Has_CommSI'] = (merged_gdf['Comm_SIP'] == 'Community SIP')
        essential_cols.append('Has_CommSI')
    
    # *** IMPORTANT: ADD ALL DISTRICT RECOMMENDATION COLUMNS ***
    print("   Adding all District Recommendation columns...")
    
    # Get all columns from the processed district recommendations that are not already included
    district_rec_cols = []
    for col in merged_gdf.columns:
        # Skip columns we've already handled or are temporary
        skip_cols = ['geometry', 'match_key', 'District_Clean', 'Adaptation_New', 'Mitigation_New', 
                    'Replacement_New', 'Overall_Potential', 'Community_SIP', 'State', 'District',
                    'Adapt', 'Mitigate', 'Replace', 'General_SI', 'Comm_SIP', 'State_Name', 
                    'Dist_Name', 'Has_CommSI'] + [c for c in gdf.columns if c != 'geometry']
        
        if col not in skip_cols and col not in essential_cols:
            # This is likely a district recommendation column
            district_rec_cols.append(col)
            essential_cols.append(col)
    
    print(f"   ✅ Found {len(district_rec_cols)} district recommendation columns to include:")
    for col in district_rec_cols[:10]:  # Show first 10
        print(f"      - {col}")
    if len(district_rec_cols) > 10:
        print(f"      ... and {len(district_rec_cols) - 10} more")
    
    # Select all essential columns
    final_gdf = merged_gdf[essential_cols].copy()
    
    # Fill NaN values in suitability columns
    for col in ['Adapt', 'Mitigate', 'Replace', 'General_SI']:
        if col in final_gdf.columns:
            final_gdf[col] = final_gdf[col].fillna('No Data')
    
    # Fill Community SIP
    if 'Comm_SIP' in final_gdf.columns:
        final_gdf['Comm_SIP'] = final_gdf['Comm_SIP'].fillna('')
    
    if 'Has_CommSI' in final_gdf.columns:
        final_gdf['Has_CommSI'] = final_gdf['Has_CommSI'].fillna(False)
    
    # Fill NaN values in district recommendation columns with appropriate defaults
    for col in district_rec_cols:
        if col in final_gdf.columns:
            if final_gdf[col].dtype == 'object':
                final_gdf[col] = final_gdf[col].fillna('N/A')
            else:
                final_gdf[col] = final_gdf[col].fillna(0)
    
    print(f"   ✅ Final columns count: {len(final_gdf.columns)}")
    print(f"   Column names: {list(final_gdf.columns)}")
    print(f"   Column name lengths: {[f'{col}({len(col)})' for col in final_gdf.columns]}")
    
    # Check for any remaining duplicates
    duplicate_cols = final_gdf.columns[final_gdf.columns.duplicated()].tolist()
    if duplicate_cols:
        print(f"   ⚠️  Warning: Duplicate columns found: {duplicate_cols}")
        final_gdf = final_gdf.loc[:, ~final_gdf.columns.duplicated()]
    
    # 6. Save the new shapefile
    print("\n6. Saving new shapefile...")
    
    output_path = "true_solar_suitability"
    
    try:
        final_gdf.to_file(f"{output_path}.shp")
        print(f"   ✅ Successfully saved: {output_path}.shp")
        
        # List all created files
        created_files = []
        for ext in ['.shp', '.shx', '.dbf', '.prj', '.cpg']:
            file_path = f"{output_path}{ext}"
            if os.path.exists(file_path):
                created_files.append(file_path)
        
        print(f"   Created files: {created_files}")
        
    except Exception as e:
        print(f"   ❌ Error saving shapefile: {e}")
        return False
    
    # 7. Generate summary report
    print("\n7. Summary Report:")
    print("="*50)
    
    for objective in ['Adapt', 'Mitigate', 'Replace', 'General_SI']:
        if objective in final_gdf.columns:
            value_counts = final_gdf[objective].value_counts()
            print(f"\n{objective}:")
            for value, count in value_counts.items():
                percentage = (count / len(final_gdf)) * 100
                print(f"   {value}: {count} ({percentage:.1f}%)")
    
    if 'Has_CommSIP' in final_gdf.columns:
        community_sip_count = final_gdf['Has_CommSIP'].sum()
        print(f"\nCommunity SIP Districts: {community_sip_count}")
    
    print(f"\nTotal Features: {len(final_gdf)}")
    print("="*50)
    
    return True

def update_app_for_new_shapefile():
    """
    Updates the app.py to use the new shapefile and add Community SIP checkbox
    """
    print("\n=== Updating App Configuration ===")
    
    print("✅ New shapefile created successfully!")
    print("📝 To use the new data in your app:")
    print("   1. Update shapefile path in app.py to 'true_solar_suitability.shp'")
    print("   2. Update column names in your app.py categories dictionary:")
    print("      categories = {")
    print("          'Adapt': 'Adaptation',")
    print("          'Mitigate': 'Mitigation',")
    print("          'Replace': 'Replacement',")
    print("          'General_SI': 'General SI'")
    print("      }")
    print("   3. Add Community SIP checkbox using 'Has_CommSIP' column")
    print("   4. The new shapefile has column names under 10 characters for compatibility")
    print("\nColumn Mapping:")
    print("   - Adapt = Adaptation suitability")
    print("   - Mitigate = Mitigation suitability") 
    print("   - Replace = Replacement suitability")
    print("   - General_SI = General Solar Initiative")
    print("   - Has_CommSIP = Community SIP availability (True/False)")

if __name__ == "__main__":
    success = create_true_solar_suitability_shapefile()
    if success:
        update_app_for_new_shapefile()
    else:
        print("\n❌ Failed to create new shapefile. Please check the error messages above.")