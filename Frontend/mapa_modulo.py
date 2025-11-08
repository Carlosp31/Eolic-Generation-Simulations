import customtkinter as ctk
from tkintermapview import TkinterMapView
from CTkMessagebox import CTkMessagebox
from Frontend.nasa_api import descargar_datos_nasa, validar_coordenadas, es_mar_o_tierra
import pandas as pd
import numpy as np
from floris import TimeSeries


class MapaManager:
    def __init__(self, parent, tab_mapa):
        self.parent = parent
        self.tab_mapa = tab_mapa
        self.selected_coords = None
        self.marker = None

        # Crear mapa
        self.map_widget = TkinterMapView(self.tab_mapa, corner_radius=10)
        self.map_widget.pack(expand=True, fill="both")
        self.map_widget.set_position(4.7110, -74.0721)  # Bogotá
        self.map_widget.set_zoom(5)

        # Evento de clic
        self.map_widget.add_left_click_map_command(self.click_mapa)

    def click_mapa(self, coords):
        self.actualizar_campos_y_mapa(*coords)

    def actualizar_campos_y_mapa(self, lat, lon):
        self.selected_coords = (lat, lon)
        self.parent.coord_label.configure(
            text=f"Coordenadas seleccionadas:\nLat: {lat:.5f}\nLon: {lon:.5f}"
        )
        self.parent.lat_entry.delete(0, "end")
        self.parent.lon_entry.delete(0, "end")
        self.parent.lat_entry.insert(0, f"{lat:.5f}")
        self.parent.lon_entry.insert(0, f"{lon:.5f}")

        if self.marker:
            self.marker.delete()
        self.marker = self.map_widget.set_marker(lat, lon, text="Posible Ubicación")

    def actualizar_mapa_desde_campos(self, event=None):
        lat, lon = validar_coordenadas(self.parent.lat_entry.get(), self.parent.lon_entry.get())
        if lat is not None and lon is not None:
            self.actualizar_campos_y_mapa(lat, lon)
            self.map_widget.set_position(lat, lon)

    def confirmar_coordenadas(self):
        lat, lon = validar_coordenadas(self.parent.lat_entry.get(), self.parent.lon_entry.get())
        if lat is None or lon is None:
            CTkMessagebox(title="❌ Error", message="Debe ingresar coordenadas válidas.")
            return

        # ✅ Validar que las coordenadas estén en el mar/oceáno
        es_mar = es_mar_o_tierra(lat, lon)
        if es_mar is None:
            CTkMessagebox(
                title="⚠️ Aviso",
                message="No se pudo verificar si la coordenada está en tierra o mar. Inténtalo nuevamente."
            )
            return
        elif not es_mar:
            CTkMessagebox(
                title="🏝️ Coordenada no válida",
                message="Las coordenadas seleccionadas están en tierra firme.\nSelecciona un punto sobre el mar u océano."
            )
            return

        # Si está en el mar, continuar
        self.selected_coords = (lat, lon)
        self.map_widget.set_position(lat, lon)

        if self.marker:
            self.marker.delete()

        self.marker = self.map_widget.set_marker(lat, lon, text="Parque Eólico Offshore")

        CTkMessagebox(
            title="✅ Coordenadas confirmadas",
            message=f"Ubicación seleccionada sobre el mar:\nLat: {lat:.5f}\nLon: {lon:.5f}"
        )

    def descargar_datos(self):
        if not self.selected_coords:
            CTkMessagebox(title="⚠️ Atención", message="Primero selecciona las coordenadas del parque.")
            return

        descargar_datos_nasa(*self.selected_coords)
        try:
            df = pd.read_csv("Frontend/nasa_wind_data.csv", skiprows=14)
            wind_directions = df["WD50M"].to_numpy()
            wind_speeds = df["WS50M"].to_numpy()
            turbulence_intensities = 0.06 * np.ones(len(df))

            time_series = TimeSeries(
                wind_directions=wind_directions,
                wind_speeds=wind_speeds,
                turbulence_intensities=turbulence_intensities
            )
            time_series.assign_ti_using_IEC_method(Iref=0.07)

            self.parent.time_series = time_series
            CTkMessagebox(
                title="✅ Descarga exitosa",
                message=f"Datos cargados correctamente.\nFilas: {len(df)}"
            )

        except Exception as e:
            CTkMessagebox(
                title="❌ Error",
                message=f"No se pudo leer el CSV.\n{e}"
            )
