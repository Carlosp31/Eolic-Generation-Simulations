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
        with open("nasa_wind_data.csv", "wb") as f:
            f.write(response.content)
        CTkMessagebox(title="✅ Éxito", message="Datos descargados correctamente en nasa_wind_data.csv")
    except Exception as e:
        CTkMessagebox(title="❌ Error", message=f"No se pudo descargar: {e}")
