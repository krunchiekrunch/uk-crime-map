# API Docs: https://data.police.uk/docs/method/crime-street

# pip install requests folium
import folium
import requests
import math

# config this
center_lat = 51.47130793789167
center_lng = -0.46068137983214263
radius_km = 10 # you might need to turn this down if it gives an error
data_month = "2025-02" # YYYY-MM
export_filename = "crimedata.html"

# generate a polygon area for the data
def generate_polygon(center_lat, center_lng, radius_km, num_points=36):
    earth_radius = 6371.0
    radius_rad = radius_km / earth_radius
    polygon_coords = []
    
    for i in range(num_points):
        angle = i * (360 / num_points)
        angle_rad = math.radians(angle)
        
        lat = center_lat + (radius_rad * math.cos(angle_rad)) * (180 / math.pi)
        lng = center_lng + (radius_rad * math.sin(angle_rad)) * (180 / math.pi) / math.cos(math.radians(center_lat))
        
        polygon_coords.append([lat, lng])
    
    return polygon_coords

# generate polygon coordinates
polygon_coords = generate_polygon(center_lat, center_lng, radius_km)

# api
polygon_str = ":".join([f"{lat},{lng}" for lat, lng in polygon_coords])
url = f"https://data.police.uk/api/crimes-street/all-crime?date={data_month}&poly={polygon_str}"
response = requests.get(url)
data = response.json()

# generate map
m = folium.Map(location=[center_lat, center_lng], zoom_start=16)
folium.Polygon(locations=polygon_coords, color='blue', fill=True, fill_opacity=0.1).add_to(m)

# track added marker locations to avoid overlap
added_locations = set()

# adjust marker location if it overlaps
def adjust_marker_location(lat, lng):
    adjustment_factor = 0.00005  # small adjustment factor on longitude
    while (lat, lng) in added_locations:
        lng += adjustment_factor
    added_locations.add((lat, lng))
    return lat, lng

# leaflet marker
for crime in data:
    location = crime['location']
    outcome = crime['outcome_status']['category'] if crime['outcome_status'] else "No outcome available"
    location_type = location.get('location_type', 'Unknown')
    street_id = location['street'].get('id', 'Unknown')
    street_name = location['street'].get('name', 'Unknown')
    month = crime.get('month', 'Unknown')
    
    # popup box content
    popup_content = f"""
    <b>Category:</b> {crime['category'].replace('-', ' ').title()}<br>
    <b>Location Type:</b> {location_type.title()}<br>
    <b>Street ID:</b> {street_id}<br>
    <b>Street Name:</b> {street_name}<br>
    <b>Outcome:</b> {outcome}<br>
    <b>Month:</b> {month}<br>
    """
    
    lat, lng = float(location['latitude']), float(location['longitude'])
    lat, lng = adjust_marker_location(lat, lng)
    
    # CircleMarker popup
    folium.CircleMarker(
        location=[lat, lng],
        radius=5,
        color='red',
        fill=True,
        fill_opacity=0.6,
        popup=folium.Popup(popup_content, max_width=300)
    ).add_to(m)

m.save(export_filename)
print("Web map exported as", export_filename)

# display when the data was last updated
# https://data.police.uk/docs/method/crime-last-updated
response = requests.get("https://data.police.uk/api/crime-last-updated")

if response.status_code == 200:
    data = response.json()
    print("Crime data last updated on:", data['date'])
else:
    print(f"Failed to retrieve update date: HTTP {response.status_code}")