import requests
from CTkMessagebox import CTkMessagebox

def validar_coordenadas(lat_text, lon_text):
    """Convierte texto a floats; devuelve (lat, lon) o (None, None) si falla."""
    try:
        lat = float(lat_text.strip())
        lon = float(lon_text.strip())
        return lat, lon
    except Exception:
        return None, None
from geopy.geocoders import Nominatim
from geopy.exc import GeocoderTimedOut, GeocoderUnavailable

def es_mar_o_tierra(lat, lon):
    """
    Retorna True si el punto está sobre el mar u océano,
    False si está sobre tierra firme.
    None si no se puede determinar.
    """
    geolocator = Nominatim(user_agent="wind_farm_locator")
    try:
        location = geolocator.reverse((lat, lon), language="en", exactly_one=True, timeout=10)
        if location is None:
            return True  # Sin datos -> probablemente mar

        address = location.raw.get("address", {})
        if "ocean" in address or "sea" in address:
            return True   # Mar u océano
        if "country" in address:
            return False  # Tierra firme
        return True
    except (GeocoderTimedOut, GeocoderUnavailable):
        return None



def descargar_datos_nasa(lat, lon):
    """Descarga datos de viento desde la API NASA POWER."""
    url = (
        f"https://power.larc.nasa.gov/api/temporal/hourly/point?"
        f"start=20240101&end=20250101"
        f"&latitude={lat}&longitude={lon}"
        "&community=re"
        "&parameters=WD50M,WS50M"
        "&format=csv"
        "&units=metric"
        "&user=carlos"
        "&header=true"
        "&time-standard=utc"
        "&site-elevation=0"
        "&wind-elevation=100"
        "&wind-surface=openwater"
    )

    try:
        response = requests.get(url)
        response.raise_for_status()
        with open("Frontend/nasa_wind_data.csv", "wb") as f:
            f.write(response.content)
        CTkMessagebox(title="✅ Éxito", message="Datos descargados correctamente en nasa_wind_data.csv")
    except Exception as e:
        CTkMessagebox(title="❌ Error", message=f"No se pudo descargar: {e}")
