import customtkinter as ctk
from tkintermapview import TkinterMapView
from CTkMessagebox import CTkMessagebox
import requests

# Configuración global
ctk.set_appearance_mode("dark")
ctk.set_default_color_theme("green")


class EolisimApp(ctk.CTk):
    def __init__(self):
        super().__init__()

        # Ventana principal
        self.title("Eolisim - Simulación de Parques Eólicos")
        self.geometry("1200x700")

        # --- Sidebar (menú lateral) ---
        self.sidebar = ctk.CTkFrame(self, width=220, corner_radius=0)
        self.sidebar.pack(side="left", fill="y")

        # Título / logo
        self.logo = ctk.CTkLabel(self.sidebar, text="🌬️ Eolisim", font=ctk.CTkFont(size=20, weight="bold"))
        self.logo.pack(pady=20)

        # Entradas de coordenadas
        coord_frame = ctk.CTkFrame(self.sidebar)
        coord_frame.pack(pady=10)

        ctk.CTkLabel(coord_frame, text="Latitud:").grid(row=0, column=0, padx=5, pady=5)
        self.lat_entry = ctk.CTkEntry(coord_frame, width=120)
        self.lat_entry.grid(row=0, column=1, padx=5, pady=5)

        ctk.CTkLabel(coord_frame, text="Longitud:").grid(row=1, column=0, padx=5, pady=5)
        self.lon_entry = ctk.CTkEntry(coord_frame, width=120)
        self.lon_entry.grid(row=1, column=1, padx=5, pady=5)

        # Botón de confirmación
        confirmar_btn = ctk.CTkButton(
            self.sidebar,
            text="✅ Confirmar ubicación",
            command=self.confirmar_coordenadas
        )
        confirmar_btn.pack(pady=10)

        # Botón para descargar datos NASA
        descargar_btn = ctk.CTkButton(
            self.sidebar,
            text="📥 Descargar Datos NASA",
            command=self.descargar_datos_nasa
        )
        descargar_btn.pack(pady=10)

        # Etiqueta de coordenadas seleccionadas
        self.coord_label = ctk.CTkLabel(self.sidebar, text="Coordenadas: (sin seleccionar)", wraplength=180)
        self.coord_label.pack(pady=15)

        # --- Área principal ---
        self.main_area = ctk.CTkFrame(self, corner_radius=10)
        self.main_area.pack(expand=True, fill="both", padx=10, pady=10)

        # Mapa (ocupa todo el espacio disponible)
        self.map_widget = TkinterMapView(self.main_area, corner_radius=10)
        self.map_widget.pack(expand=True, fill="both")  # 👈 Ajuste importante
        self.map_widget.set_position(4.7110, -74.0721)  # Bogotá por defecto
        self.map_widget.set_zoom(5)

        # Eventos y variables
        self.map_widget.add_left_click_map_command(self.click_mapa)
        self.selected_coords = None
        self.marker = None

        # Vincular eventos de escritura manual
        self.lat_entry.bind("<FocusOut>", self.actualizar_mapa_desde_campos)
        self.lon_entry.bind("<FocusOut>", self.actualizar_mapa_desde_campos)

    # --- Evento click en mapa ---
    def click_mapa(self, coords):
        lat, lon = coords
        self.actualizar_campos_y_mapa(lat, lon)

    # --- Actualizar campos, etiqueta y marcador ---
    def actualizar_campos_y_mapa(self, lat, lon):
        self.selected_coords = (lat, lon)
        self.coord_label.configure(text=f"Coordenadas seleccionadas:\nLat: {lat:.5f}\nLon: {lon:.5f}")

        self.lat_entry.delete(0, "end")
        self.lon_entry.delete(0, "end")
        self.lat_entry.insert(0, f"{lat:.5f}")
        self.lon_entry.insert(0, f"{lon:.5f}")

        # Actualizar marcador
        if self.marker:
            self.marker.delete()
        self.marker = self.map_widget.set_marker(lat, lon, text="Parque Eólico")

    # --- Si el usuario escribe coordenadas manualmente ---
    def actualizar_mapa_desde_campos(self, event=None):
        try:
            lat_text = self.lat_entry.get().strip()
            lon_text = self.lon_entry.get().strip()
            if not lat_text or not lon_text:
                return

            lat = float(lat_text)
            lon = float(lon_text)
            self.actualizar_campos_y_mapa(lat, lon)
            self.map_widget.set_position(lat, lon)
        except ValueError:
            pass

    # --- Confirmar coordenadas ---
    def confirmar_coordenadas(self):
        try:
            if not self.lat_entry.get() or not self.lon_entry.get():
                raise ValueError("Debe seleccionar o ingresar coordenadas.")
            lat = float(self.lat_entry.get())
            lon = float(self.lon_entry.get())
            self.selected_coords = (lat, lon)
            CTkMessagebox(title="✅ Coordenadas confirmadas", message=f"Ubicación seleccionada:\nLat: {lat}\nLon: {lon}")
        except Exception as e:
            CTkMessagebox(title="❌ Error", message=f"Entrada inválida: {e}")

    # --- Descargar datos NASA POWER ---
    def descargar_datos_nasa(self):
        if not self.selected_coords:
            CTkMessagebox(title="⚠️ Atención", message="Primero selecciona las coordenadas del parque.")
            return

        lat, lon = self.selected_coords
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


if __name__ == "__main__":
    app = EolisimApp()
    app.mainloop()

