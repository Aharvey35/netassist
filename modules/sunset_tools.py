import requests
from datetime import datetime
from zoneinfo import ZoneInfo

def run():
    city = input("Enter city (i.e. 'Upland' or 'Paris'): ").strip()
    region = input("Enter state or region (i.e. 'CA' or 'Île-de-France'): ").strip()
    country = input("Enter country (i.e. 'USA' or 'France'): ").strip()

    if not city or not country:
        print("City and country are required. Aborting.")
        return

    # Construct location string
    if region:
        loc = f"{city}, {region}, {country}"
    else:
        loc = f"{city}, {country}"

    try:
        geo_resp = requests.get(
            'https://nominatim.openstreetmap.org/search',
            params={'q': loc, 'format': 'json', 'limit': 1},
            headers={'User-Agent': 'NetAssist'}
        )
        geo_resp.raise_for_status()
        data = geo_resp.json()
        if not data:
            print(f"Location '{loc}' not found.")
            return

        display_name = data[0]['display_name']
        lat = data[0]['lat']
        lon = data[0]['lon']

        print(f"\nResolved location: {display_name}")

        # Only validate region if country is USA
        if country.strip().upper() in ["USA", "US", "UNITED STATES"]:
            state_abbr = region.strip().upper()
            if state_abbr in US_STATE_MAP:
                expected = US_STATE_MAP[state_abbr]
                if state_abbr not in display_name and expected not in display_name:
                    print("  Warning: Geocoded location doesn't appear to match the specified state.")
                    retry = input("Do you want to try again? (y/n): ").strip().lower()
                    if retry == 'y':
                        return run()
                    else:
                        return

    except Exception as e:
        print(f"Error fetching geolocation: {e}")
        return

    # Get sunset time
    try:
        sun_resp = requests.get(
            'https://api.sunrise-sunset.org/json',
            params={'lat': lat, 'lng': lon, 'formatted': 0}
        )
        sun_resp.raise_for_status()
        sun_data = sun_resp.json()
        if sun_data['status'] != 'OK':
            print(f"Error retrieving sunset time: {sun_data['status']}")
            return

        utc_sunset = sun_data['results']['sunset']
        dt_utc = datetime.fromisoformat(utc_sunset).replace(tzinfo=ZoneInfo("UTC"))

        # For USA, assume Pacific unless extended logic is added
        if country.strip().upper() in ["USA", "US", "UNITED STATES"]:
            local_dt = dt_utc.astimezone(ZoneInfo("America/Los_Angeles"))
        else:
            local_dt = dt_utc  # Show UTC for now (or extend with proper geo-based TZ lookup)

        local = local_dt.strftime('%-I:%M %p')
        print(f"Sunset in {city.title()}, {region.upper()} today is at {local} (local time)")

    except Exception as e:
        print(f"Error fetching sunset data: {e}")


# Abbreviation → full name for U.S. states
US_STATE_MAP = {
    "CA": "California", "NY": "New York", "TX": "Texas", "FL": "Florida", "WA": "Washington",
    "AZ": "Arizona", "NV": "Nevada", "IL": "Illinois", "GA": "Georgia", "NC": "North Carolina",
    "CO": "Colorado", "NJ": "New Jersey", "PA": "Pennsylvania", "OH": "Ohio", "MI": "Michigan",
    # Add more as needed
}
