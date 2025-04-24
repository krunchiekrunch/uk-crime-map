# API Docs: https://data.police.uk/docs/method/stops-street/

# pip install requests folium plotly pandas
import folium
import requests
import math
import plotly.express as px
import plotly.subplots as sp
import plotly.graph_objects as go
from collections import Counter
import pandas as pd

# config this
center_lat = 51.47130793789167
center_lng = -0.46068137983214263
radius_km = 10
data_month = "2025-02" # YYYY-MM
map_filename = "map_stopandsearch.html"
graph_filename = "graphs_stopandsearch.html"

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

polygon_coords = generate_polygon(center_lat, center_lng, radius_km)
polygon_str = ":".join([f"{lat},{lng}" for lat, lng in polygon_coords])
url = f"https://data.police.uk/api/stops-street?date={data_month}&poly={polygon_str}"
response = requests.get(url)
data = response.json()

# generate map
m = folium.Map(location=[center_lat, center_lng], zoom_start=16)
folium.Polygon(locations=polygon_coords, color='blue', fill=True, fill_opacity=0.1).add_to(m)

# track added marker locations to avoid overlap
added_locations = set()

# adjust marker location if it overlaps
def adjust_marker_location(lat, lng):
    adjustment_factor = 0.00005
    while (lat, lng) in added_locations:
        lng += adjustment_factor
    added_locations.add((lat, lng))
    return lat, lng

# For charts
chart_data = {
    "gender": [],
    "age_range": [],
    "self_defined_ethnicity": [],
    "officer_defined_ethnicity": [],
    "legislation": [],
    "object_of_search": [],
    "outcome": [],
    "outcome_linked_to_object_of_search": [],
    "removal_of_more_than_outer_clothing": []
}

for stop in data:
    location = stop['location']
    street_name = location['street'].get('name', 'Unknown')
    
    
    for key in chart_data:
        chart_data[key].append(stop.get(key, 'Unknown'))
    
    # popup box content
    popup_content = f"""
    <b>Type:</b> {stop.get('type', 'Unknown')}<br>
    <b>Involved Person:</b> {stop.get('involved_person', 'Unknown')}<br>
    <b>Date & Time:</b> {stop.get('datetime', 'Unknown')}<br>
    <b>Operation:</b> {stop.get('operation', 'None')}<br>
    <b>Operation Name:</b> {stop.get('operation_name', 'None')}<br>
    <b>Street Name:</b> {street_name}<br>
    <b>Gender:</b> {stop.get('gender', 'Unknown')}<br>
    <b>Age Range:</b> {stop.get('age_range', 'Unknown')}<br>
    <b>Self-defined Ethnicity:</b> {stop.get('self_defined_ethnicity', 'Unknown')}<br>
    <b>Officer-defined Ethnicity:</b> {stop.get('officer_defined_ethnicity', 'Unknown')}<br>
    <b>Legislation:</b> {stop.get('legislation', 'Unknown')}<br>
    <b>Object of Search:</b> {stop.get('object_of_search', 'Unknown')}<br>
    <b>Outcome:</b> {stop.get('outcome', 'Unknown')}<br>
    <b>Outcome Linked to Object of Search:</b> {stop.get('outcome_linked_to_object_of_search', 'Unknown')}<br>
    <b>Removal of More Than Outer Clothing:</b> {stop.get('removal_of_more_than_outer_clothing', 'Unknown')}<br>
    """

    lat, lng = float(location['latitude']), float(location['longitude'])
    lat, lng = adjust_marker_location(lat, lng)

    # CircleMarker popup
    folium.CircleMarker(
        location=[lat, lng],
        radius=5,
        color='purple',
        fill=True,
        fill_opacity=0.6,
        popup=folium.Popup(popup_content, max_width=300)
    ).add_to(m)

m.save(map_filename)
print("Web map exported as", map_filename)

# generate graphs
fig = sp.make_subplots(
    rows=9, cols=1,
    subplot_titles=[k.replace("_", " ").title() for k in chart_data],
    specs=[[{"type": "domain"}]] * 9
)

row = 1
max_slices = 0  # to find the required height
for key, values in chart_data.items():
    counts = Counter(values)
    labels, values = zip(*counts.items())

    max_slices = max(max_slices, len(labels))  # track the largest chart

    fig.add_trace(
        go.Pie(
            labels=labels,
            values=values,
            name=key,
            textinfo='label+percent',
            showlegend=False
        ),
        row=row, col=1
    )
    row += 1

# dynamically adjust height: 300 per chart + extra if slices are many
estimated_height = 300 * 9 + (max_slices * 100)

fig.update_layout(
    title_text="Stop and Search Breakdown",
    height=estimated_height,
    margin=dict(t=100, b=50)
)
fig.write_html(graph_filename)
print("Graphs exported as", graph_filename)

# display when the data was last updated
# https://data.police.uk/docs/method/crime-last-updated
response = requests.get("https://data.police.uk/api/crime-last-updated")
if response.status_code == 200:
    data = response.json()
    print("Crime data last updated on:", data['date'])
else:
    print(f"Failed to retrieve update date: HTTP {response.status_code}")