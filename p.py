import json
import pandas as pd
import geopandas as gpd
import folium
from folium.features import GeoJsonTooltip
import requests

def get_wa_counties():
    """Download Washington county boundaries from the US Census Bureau"""
    try:
        # Use Census Bureau's cartographic boundary files
        # This URL provides detailed county boundaries, not just bounding boxes
        api_url = "https://raw.githubusercontent.com/plotly/datasets/master/geojson-counties-fips.json"
        
        # Make the request
        response = requests.get(api_url)
        
        if response.status_code == 200:
            # Load the full US counties GeoJSON
            all_counties = response.json()
            
            # Get Washington state FIPS codes (53 is WA state code)
            wa_counties_geojson = {
                "type": "FeatureCollection",
                "features": [
                    f for f in all_counties["features"] 
                    if f["properties"]["STATE"] == "53"
                ]
            }
            
            # Convert county FIPS codes to county names using a standard mapping
            county_names = {
                "53001": "Adams", "53003": "Asotin", "53005": "Benton", 
                "53007": "Chelan", "53009": "Clallam", "53011": "Clark",
                "53013": "Columbia", "53015": "Cowlitz", "53017": "Douglas", 
                "53019": "Ferry", "53021": "Franklin", "53023": "Garfield", 
                "53025": "Grant", "53027": "Grays Harbor", "53029": "Island",
                "53031": "Jefferson", "53033": "King", "53035": "Kitsap", 
                "53037": "Kittitas", "53039": "Klickitat", "53041": "Lewis",
                "53043": "Lincoln", "53045": "Mason", "53047": "Okanogan", 
                "53049": "Pacific", "53051": "Pend Oreille", "53053": "Pierce",
                "53055": "San Juan", "53057": "Skagit", "53059": "Skamania", 
                "53061": "Snohomish", "53063": "Spokane", "53065": "Stevens", 
                "53067": "Thurston", "53069": "Wahkiakum", "53071": "Walla Walla",
                "53073": "Whatcom", "53075": "Whitman", "53077": "Yakima"
            }
            
            # Add county names to properties
            for feature in wa_counties_geojson["features"]:
                fips = feature["properties"]["COUNTY"]
                state_fips = feature["properties"]["STATE"]
                full_fips = state_fips + fips
                feature["properties"]["NAME"] = county_names.get(full_fips, "Unknown")
                feature["properties"]["NAMELSAD"] = county_names.get(full_fips, "Unknown") + " County"
            
            # Convert to GeoDataFrame
            gdf = gpd.GeoDataFrame.from_features(wa_counties_geojson, crs="EPSG:4326")
            return gdf
        else:
            print(f"API request failed with status code: {response.status_code}")
            raise Exception("Failed to fetch county data from API")
            
    except Exception as e:
        print(f"Error getting county data: {e}")
        raise

# Main function to generate the map
def create_wa_minimum_wage_map():
    # Get the county data from the API
    counties_gdf = get_wa_counties()
    
    # Add minimum wage data (in CAD)
    counties_gdf['min_wage_numeric'] = 23.70  # Default for all counties
    counties_gdf.loc[counties_gdf['NAME'] == 'King', 'min_wage_numeric'] = 30.09
    counties_gdf.loc[counties_gdf['NAME'] == 'Whatcom', 'min_wage_numeric'] = 26.54

    # Add descriptive wage text
    counties_gdf['min_wage_cad'] = counties_gdf['min_wage_numeric'].astype(str) + " Canadian Dollars an hour"
    counties_gdf.loc[counties_gdf['NAME'] == 'Whatcom', 'min_wage_cad'] += " starting May 1st"

    # Create the interactive map
    m = folium.Map(location=[47.5, -120.5], zoom_start=7, tiles='CartoDB positron')

    # Define a function to color counties based on minimum wage
    def style_function(feature):
        wage = feature['properties']['min_wage_numeric']
        # Use different shades of gold from light to dark
        if wage == 30.09:  # King County (richest)
            return {'fillColor': '#ffd700', 'color': '#000000', 'weight': 1, 'fillOpacity': 0.7}  # Rich gold
        elif wage == 26.54:  # Whatcom County (middle)
            return {'fillColor': '#f5c855', 'color': '#000000', 'weight': 1, 'fillOpacity': 0.7}  # Medium gold
        else:  # All other counties (poorest)
            return {'fillColor': '#ffeeba', 'color': '#000000', 'weight': 1, 'fillOpacity': 0.7}  # Light gold

    # Add tooltip to show information when hovering
    tooltip = GeoJsonTooltip(
        fields=['NAME', 'min_wage_cad'],
        aliases=['County: ', 'Minimum Wage: '],
        style=('background-color: white; color: #333333; font-family: arial; font-size: 12px; padding: 10px;')
    )

    # Add the colored GeoJSON to the map
    folium.GeoJson(
        counties_gdf.__geo_interface__,
        name='Washington Counties',
        style_function=style_function,
        tooltip=tooltip
    ).add_to(m)

    # Add a legend
    legend_html = '''
    <div style="position: fixed; bottom: 50px; left: 50px; width: 300px; height: 130px; 
    background-color: white; border:2px solid grey; z-index:9999; font-size:14px;
    padding: 10px; border-radius: 5px;">
    <b>Minimum Wage (CAD/hour)</b> <br>
    <i style="background: #ffd700; width: 15px; height: 15px; display: inline-block;"></i> King County: 30.09 <br>
    <i style="background: #f5c855; width: 15px; height: 15px; display: inline-block;"></i> Whatcom County: 26.54 (starting May 1st) <br>
    <i style="background: #ffeeba; width: 15px; height: 15px; display: inline-block;"></i> All other counties: 23.70
    </div>
    '''
    m.get_root().html.add_child(folium.Element(legend_html))

    # Add a title
    title_html = '''
    <h3 align="center" style="font-size:20px"><b>Minimum Wage by County in Washington State (CAD)</b></h3>
    <p align="center" style="font-size:14px">All Counties in Gold Shades - Richer Counties in Darker Gold</p>
    '''
    m.get_root().html.add_child(folium.Element(title_html))

    # Save to HTML file
    output_file = 'washington_minimum_wage_cad_map.html'
    m.save(output_file)

    print(f"Interactive map has been saved as '{output_file}'")
    return output_file

# Run the function
if __name__ == "__main__":
    create_wa_minimum_wage_map()