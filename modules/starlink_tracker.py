import requests
from datetime import datetime
import random
import math

CELESTRAK_URL = "https://celestrak.org/NORAD/elements/gp.php?GROUP=starlink&FORMAT=tle"
GEOCODE_URL = "https://geocode.maps.co/reverse"

HEADERS = {
    "User-Agent": "NetAssist Satellite Tracker"
}

def run():
    try:
        print("\nFetching real-time Starlink satellite info...")

        satellites = fetch_starlink_tles()
        sat_name, tle1, tle2 = random.choice(satellites)

        lat, lon, alt = extract_position_from_tle(tle2)
        location = resolve_location_name(lat, lon)

        print(f"\nSatellite: {sat_name}")
        print(f"TLE Line 1 : {tle1}")
        print(f"TLE Line 2 : {tle2}")
        print(f"\n  Location : {lat:.2f}, {lon:.2f}  ({location})")
        print(f"  Latitude : {lat:.2f}°")
        print(f"  Longitude: {lon:.2f}°")
        print(f"  Altitude : {alt:.2f} km")
        print("  UTC Time :", datetime.utcnow().strftime("%A, %B %d, %Y — %H:%M UTC"))

    except Exception as e:
        print(f"Error fetching Starlink data: {e}")

def fetch_starlink_tles():
    resp = requests.get(CELESTRAK_URL, headers=HEADERS)
    resp.raise_for_status()
    lines = resp.text.strip().splitlines()

    satellites = []
    for i in range(0, len(lines), 3):
        name = lines[i].strip()
        tle1 = lines[i + 1].strip()
        tle2 = lines[i + 2].strip()
        satellites.append((name, tle1, tle2))
    return satellites

def extract_position_from_tle(tle_line2):
    parts = tle_line2.split()
    inclination = float(parts[2])
    raan = float(parts[3])
    mean_anomaly = float(parts[5])
    mean_motion = float(parts[7])

    lat = inclination * math.sin(math.radians(mean_anomaly))
    lon = (raan + mean_anomaly) % 360
    if lon > 180:
        lon -= 360

    altitude = 6371 + (1326 / mean_motion)
    return lat, lon, altitude

def resolve_location_name(lat, lon):
    try:
        resp = requests.get(
            GEOCODE_URL,
            params={"lat": lat, "lon": lon, "format": "json"},
            headers=HEADERS,
            timeout=10
        )
        data = resp.json()
        address = data.get("address", {})

        location = (
            address.get("city") or
            address.get("town") or
            address.get("village") or
            address.get("state") or
            address.get("county") or
            address.get("country")
        )

        if not location and "display_name" in data:
            location = data["display_name"].split(",")[0].strip()

        return location or ("At Sea" if abs(lat) < 70 else "Polar Region")
    except Exception:
        return "Unknown"
