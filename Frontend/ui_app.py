import customtkinter as ctk
from tkintermapview import TkinterMapView
from CTkMessagebox import CTkMessagebox
from Frontend.nasa_api import descargar_datos_nasa, validar_coordenadas

ctk.set_appearance_mode("dark")
ctk.set_default_color_theme("green")


class EolisimApp(ctk.CTk):
    def __init__(self):
        super().__init__()
        self.title("Eolisim - Simulación de Parques Eólicos")
        self.geometry("1200x700")

        # --- Sidebar ---
        self.sidebar = ctk.CTkFrame(self, width=220, corner_radius=0)
        self.sidebar.pack(side="left", fill="y")

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

        ctk.CTkButton(self.sidebar, text="✅ Confirmar ubicación", command=self.confirmar_coordenadas).pack(pady=10)
        ctk.CTkButton(self.sidebar, text="📥 Descargar Datos NASA", command=self.descargar_datos).pack(pady=10)

        self.coord_label = ctk.CTkLabel(self.sidebar, text="Coordenadas: (sin seleccionar)", wraplength=180)
        self.coord_label.pack(pady=15)

        # --- Mapa principal ---
        self.main_area = ctk.CTkFrame(self, corner_radius=10)
        self.main_area.pack(expand=True, fill="both", padx=10, pady=10)

        self.map_widget = TkinterMapView(self.main_area, corner_radius=10)
        self.map_widget.pack(expand=True, fill="both")
        self.map_widget.set_position(4.7110, -74.0721)
        self.map_widget.set_zoom(5)

        self.map_widget.add_left_click_map_command(self.click_mapa)

        self.selected_coords = None
        self.marker = None

        # Eventos de escritura manual
        self.lat_entry.bind("<FocusOut>", self.actualizar_mapa_desde_campos)
        self.lon_entry.bind("<FocusOut>", self.actualizar_mapa_desde_campos)

    # --- Métodos GUI ---
    def click_mapa(self, coords):
        self.actualizar_campos_y_mapa(*coords)

    def actualizar_campos_y_mapa(self, lat, lon):
        self.selected_coords = (lat, lon)
        self.coord_label.configure(text=f"Coordenadas seleccionadas:\nLat: {lat:.5f}\nLon: {lon:.5f}")

        self.lat_entry.delete(0, "end")
        self.lon_entry.delete(0, "end")
        self.lat_entry.insert(0, f"{lat:.5f}")
        self.lon_entry.insert(0, f"{lon:.5f}")

        if self.marker:
            self.marker.delete()
        self.marker = self.map_widget.set_marker(lat, lon, text="Parque Eólico")

    def actualizar_mapa_desde_campos(self, event=None):
        lat, lon = validar_coordenadas(self.lat_entry.get(), self.lon_entry.get())
        if lat is not None and lon is not None:
            self.actualizar_campos_y_mapa(lat, lon)
            self.map_widget.set_position(lat, lon)

    def confirmar_coordenadas(self):
        lat, lon = validar_coordenadas(self.lat_entry.get(), self.lon_entry.get())
        if lat is None or lon is None:
            CTkMessagebox(title="❌ Error", message="Debe ingresar coordenadas válidas.")
            return
        self.selected_coords = (lat, lon)
        CTkMessagebox(title="✅ Coordenadas confirmadas", message=f"Ubicación seleccionada:\nLat: {lat}\nLon: {lon}")

    def descargar_datos(self):
        if not self.selected_coords:
            CTkMessagebox(title="⚠️ Atención", message="Primero selecciona las coordenadas del parque.")
            return
        descargar_datos_nasa(*self.selected_coords)
