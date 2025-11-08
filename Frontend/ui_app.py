import customtkinter as ctk
from Frontend.mapa_modulo import MapaManager
from Frontend.layout_modulo import LayoutManager
from Frontend.simulacion_modulo import SimulacionManager


class EolisimApp(ctk.CTk):
    def __init__(self):
        super().__init__()
        self.title("Eolisim - Simulación de Parques Eólicos")
        self.geometry("1200x700")
        ctk.set_appearance_mode("dark")
        ctk.set_default_color_theme("green")

        self.sidebar = ctk.CTkFrame(self, width=220)
        self.sidebar.pack(side="left", fill="y")
        ctk.CTkLabel(self.sidebar, text="Eolisim", font=ctk.CTkFont(size=20, weight="bold")).pack(pady=20)

        # Entradas coordenadas
        self.crear_controles_sidebar()

        # Tabs principales
        self.main_area = ctk.CTkTabview(self, corner_radius=10)
        self.main_area.pack(expand=True, fill="both", padx=10, pady=10)
        self.tab_mapa = self.main_area.add("Mapa")
        self.tab_plano = self.main_area.add("Grilla")
        self.tab_sim = self.main_area.add("Simulación")

        # Módulos
        self.mapa = MapaManager(self, self.tab_mapa)
        self.layout = LayoutManager(self, self.tab_plano)
        self.simulacion = SimulacionManager(self, self.tab_sim)

        # Turbina
        self.turbina_interna = "nrel_5MW"

    def crear_controles_sidebar(self):
        import customtkinter as ctk
        from CTkMessagebox import CTkMessagebox

        coord_frame = ctk.CTkFrame(self.sidebar)
        coord_frame.pack(pady=10)
        ctk.CTkLabel(coord_frame, text="Latitud:").grid(row=0, column=0)
        self.lat_entry = ctk.CTkEntry(coord_frame, width=120)
        self.lat_entry.grid(row=0, column=1)
        ctk.CTkLabel(coord_frame, text="Longitud:").grid(row=1, column=0)
        self.lon_entry = ctk.CTkEntry(coord_frame, width=120)
        self.lon_entry.grid(row=1, column=1)
        ctk.CTkButton(self.sidebar, text="✅ Confirmar ubicación",
                      command=self.confirmar_coordenadas).pack(pady=10)
        ctk.CTkButton(self.sidebar, text="📥 Descargar Datos NASA",
                      command=self.descargar_datos).pack(pady=10)
        self.coord_label = ctk.CTkLabel(self.sidebar, text="Coordenadas: (sin seleccionar)")
        self.coord_label.pack(pady=10)

        ctk.CTkLabel(self.sidebar, text="Tipo de turbina:").pack(pady=(15, 5))
        self.turbina_selector = ctk.CTkOptionMenu(
            self.sidebar,
            values=["NREL 5MW reference wind turbine", "IEA 10MW reference wind turbine", "IEA 15MW reference wind turbine", "Vestas V164 - 9.5MW", "Siemens Gamesa SG 8.0-167 DD", "Vestas V164-8.0MW"],
            command=self.actualizar_turbina
        )
        self.turbina_selector.pack(pady=5)
        self.turbina_selector.set("NREL 5MW reference wind turbine")

    def confirmar_coordenadas(self):
        self.mapa.confirmar_coordenadas()

    def descargar_datos(self):
        self.mapa.descargar_datos()

    def actualizar_turbina(self, seleccion):
        # Mapeo entre nombre mostrado y código interno
        mapping = {
            "NREL 5MW reference wind turbine": "nrel_5MW",
            "IEA 10MW reference wind turbine": "iea_10MW",
            "IEA 15MW reference wind turbine": "iea_15MW",
            "Vestas V164 - 9.5MW": "V164_9_5MW",
            "Siemens Gamesa SG 8.0-167 DD": "SG_8_0_167_DD",
            "Vestas V164-8.0MW": "V164_8MW"
        }

        # Mapeo entre nombre mostrado y potencia nominal en MW
        potencia_nominal = {
            "NREL 5MW reference wind turbine": 5.0,
            "IEA 10MW reference wind turbine": 10.0,
            "IEA 15MW reference wind turbine": 15.0,
            "Vestas V164 - 9.5MW": 9.5,
            "Siemens Gamesa SG 8.0-167 DD": 8.0,
            "Vestas V164-8.0MW": 8.0
        }

        # Mapeo entre nombre mostrado y tipo (referencia o real)
        tipo_turbina = {
            "NREL 5MW reference wind turbine": "Referencia",
            "IEA 10MW reference wind turbine": "Referencia",
            "IEA 15MW reference wind turbine": "Referencia",
            "Vestas V164 - 9.5MW": "Real",
            "Siemens Gamesa SG 8.0-167 DD": "Real",
            "Vestas V164-8.0MW": "Real"
        }

        # Actualizar variables internas del proyecto
        self.turbina_interna = mapping.get(seleccion, "nrel_5MW")
        self.potencia_nominal_turbina_mw = potencia_nominal.get(seleccion, 5.0)
        self.tipo_turbina = tipo_turbina.get(seleccion, "Referencia")





