import streamlit as st
import folium
from streamlit_folium import st_folium
import requests

st.set_page_config(page_title="Kraków Bike Route Builder", layout="wide")

st.title("🚴 Kraków Bike Route Builder")
st.write("Click points on the map to build a custom bike route through Kraków.")

# Kraków center coordinates (used to center the map on load)
KRAKOW_CENTER = [50.0614, 19.9366]

# st.session_state lets us remember data between reruns.
# Streamlit reruns your whole script top-to-bottom on every interaction,
# so without this, our clicked points would disappear immediately.
if "points" not in st.session_state:
    st.session_state.points = []

col1, col2 = st.columns([3, 1])

with col2:
    st.subheader("Controls")
    if st.button("Reset route"):
        st.session_state.points = []
        st.rerun()

    st.write(f"Points selected: {len(st.session_state.points)}")
    for i, p in enumerate(st.session_state.points):
        st.write(f"{i + 1}. ({p[0]:.4f}, {p[1]:.4f})")

with col1:
    m = folium.Map(location=KRAKOW_CENTER, zoom_start=13)

    # Draw a marker for every point the user has clicked so far
    for i, p in enumerate(st.session_state.points):
        folium.Marker(p, popup=f"Point {i + 1}", icon=folium.Icon(color="blue")).add_to(m)

    # Once we have 2+ points, ask OSRM (a free open-source routing engine)
    # for a real cycling route that passes through them in order.
    if len(st.session_state.points) >= 2:
        coords_str = ";".join(f"{lon},{lat}" for lat, lon in st.session_state.points)
        url = (
            f"https://router.project-osrm.org/route/v1/cycling/{coords_str}"
            "?overview=full&geometries=geojson"
        )
        try:
            resp = requests.get(url, timeout=6)
            data = resp.json()
            if data.get("code") == "Ok":
                route_coords = data["routes"][0]["geometry"]["coordinates"]
                route_latlon = [(lat, lon) for lon, lat in route_coords]
                folium.PolyLine(route_latlon, color="red", weight=4).add_to(m)
                st.session_state.last_distance = data["routes"][0]["distance"] / 1000
            else:
                st.warning("Couldn't find a bike route between those points — try different ones.")
        except Exception as e:
            st.error(f"Routing service error: {e}")

    map_data = st_folium(m, width=800, height=550)

    # st_folium returns info about map interactions, including the last click.
    # We check if it's a *new* click and, if so, add it to our list and rerun.
    if map_data and map_data.get("last_clicked"):
        clicked = (map_data["last_clicked"]["lat"], map_data["last_clicked"]["lng"])
        if clicked not in st.session_state.points:
            st.session_state.points.append(clicked)
            st.rerun()

if "last_distance" in st.session_state and len(st.session_state.points) >= 2:
    st.success(f"Total route distance: {st.session_state.last_distance:.2f} km")
