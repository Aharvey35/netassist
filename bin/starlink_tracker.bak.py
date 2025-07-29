import requests
from datetime import datetime
from sgp4.api import Satrec, jday
from geopy.geocoders import Nominatim
from math import atan2, degrees, sqrt

def run():
    print("\nFetching real-time Starlink satellite info...\n")

    try:
        tle = get_latest_starlink_tle()
        if not tle:
            print("No Starlink data available.")
            return

        name, line1, line2 = tle
        print(f"🛰️  Satellite: {name}")
        print(f"TLE Line 1 : {line1}")
        print(f"TLE Line 2 : {line2}\n")

        now = datetime.utcnow()
        jd, fr = jday(now.year, now.month, now.day, now.hour, now.minute, now.second)
        sat = Satrec.twoline2rv(line1, line2)
        e, r, v = sat.sgp4(jd, fr)

        if e != 0:
            print("Error computing satellite position.")
            return

        x, y, z = r
        lat, lon, alt = eci_to_geo(x, y, z)

        location = geolocate(lat, lon)

        print(f"📍 Location   : {location}")
        print(f"• Latitude   : {lat:.2f}°")
        print(f"• Longitude  : {lon:.2f}°")
        print(f"• Altitude   : {alt:.2f} km")
        print(f"• UTC Time   : {now.strftime('%A, %B %d, %Y — %H:%M UTC')}")

    except Exception as e:
        print(f"Error: {e}")


def get_latest_starlink_tle():
    url = "https://celestrak.org/NORAD/elements/gp.php?GROUP=starlink&FORMAT=tle"
    resp = requests.get(url)
    resp.raise_for_status()
    lines = resp.text.strip().splitlines()

    for i in range(0, len(lines), 3):
        if i + 2 < len(lines):
            return lines[i].strip(), lines[i+1].strip(), lines[i+2].strip()

    return None


def eci_to_geo(x, y, z):
    r = sqrt(x*x + y*y)
    lon = atan2(y, x)
    lat = atan2(z, r)
    alt = sqrt(x**2 + y**2 + z**2)
    return degrees(lat), degrees(lon), alt


def geolocate(lat, lon):
    try:
        geolocator = Nominatim(user_agent="netassist_starlink_locator")
        location = geolocator.reverse((lat, lon), timeout=10, language='en')

        if location and location.raw.get("address"):
            addr = location.raw["address"]
            components = [
                addr.get("city"),
                addr.get("state"),
                addr.get("country")
            ]
            return "Near " + ', '.join(filter(None, components))
        else:
            return f"{lat:.2f}, {lon:.2f}"
    except Exception:
        return f"{lat:.2f}, {lon:.2f}"
