from CTkMessagebox import CTkMessagebox
import numpy as np
from floris import FlorisModel
import floris.layout_visualization as layoutviz
from floris.flow_visualization import visualize_cut_plane
import matplotlib.pyplot as plt
from matplotlib.backends.backend_tkagg import FigureCanvasTkAgg
import tkinter as tk
import warnings
warnings.filterwarnings("ignore")


class SimulacionManager:
    def __init__(self, parent, tab_simulacion):
        self.parent = parent
        self.tab_simulacion = tab_simulacion
        self.fmodel = FlorisModel(
            r"C:\Users\DELL\Desktop\Cosas universidad sexto semestre\pf_electrica\Frontend\gch.yaml"
        )

        # Canvases de las figuras
        self.layout_canvas = None
        self.flow_canvas = None

        self.crear_interfaz()

    def crear_interfaz(self):
        import customtkinter as ctk

        # ======== Marco principal ========
        self.frame_principal = ctk.CTkFrame(self.tab_simulacion)
        self.frame_principal.pack(fill="both", expand=True, padx=10, pady=10)

        # ======== Panel izquierdo ========
        self.frame_izquierdo = ctk.CTkFrame(self.frame_principal, width=300)
        self.frame_izquierdo.pack(side="left", fill="y", padx=10, pady=10)

        # ======== Panel derecho con scroll ========
        self.frame_derecho = ctk.CTkFrame(self.frame_principal)
        self.frame_derecho.pack(side="right", fill="both", expand=True, padx=10, pady=10)

        # Canvas y Scrollbar para hacer scroll infinito
        self.canvas_derecho = tk.Canvas(self.frame_derecho, bg="#1E1E1E", highlightthickness=0)
        self.scrollbar = tk.Scrollbar(self.frame_derecho, orient="vertical", command=self.canvas_derecho.yview)
        self.frame_graficas = tk.Frame(self.canvas_derecho, bg="#1E1E1E")

        # Vincular eventos para el scroll
        self.frame_graficas.bind(
            "<Configure>",
            lambda e: self.canvas_derecho.configure(scrollregion=self.canvas_derecho.bbox("all"))
        )
        self.canvas_derecho.create_window((0, 0), window=self.frame_graficas, anchor="nw")
        self.canvas_derecho.configure(yscrollcommand=self.scrollbar.set)

        self.canvas_derecho.pack(side="left", fill="both", expand=True)
        self.scrollbar.pack(side="right", fill="y")

        # ======== Textbox de resultados ========
        self.result_text = ctk.CTkTextbox(self.frame_izquierdo, width=280, height=350)
        self.result_text.pack(pady=10)
        self.result_text.insert("end", "Resultados de simulación aparecerán aquí...\n")
        self.result_text.configure(state="disabled")

        # ======== Botón ejecutar ========
        ctk.CTkButton(
            self.frame_izquierdo,
            text="▶️ Ejecutar Simulación",
            fg_color="#2fa86f",
            command=self.ejecutar_simulacion
        ).pack(pady=15)

    def ejecutar_simulacion(self):
        if not hasattr(self.parent, "time_series"):
            CTkMessagebox(title="⚠️ Faltan datos NASA", message="Descarga los datos primero.")
            return

        layout = self.parent.layout.layout_x, self.parent.layout.layout_y
        if not self.parent.layout.layout_confirmado:
            CTkMessagebox(title="⚠️ Layout no confirmado", message="Confirma el layout primero.")
            return

        try:
            # Configurar FLORIS
            self.fmodel.set(turbine_type=[self.parent.turbina_interna])
            self.fmodel.set(layout_x=layout[0], layout_y=layout[1])
            self.fmodel.set(wind_data=self.parent.time_series)
            self.fmodel.run()

            # Potencias
            turbine_powers = self.fmodel.get_turbine_powers() / 1000.0
            farm_power = self.fmodel.get_farm_power() / 1000.0

            # AEP y pérdidas
            aep = self.fmodel.get_farm_AEP()
            self.fmodel.run_no_wake()
            aep_no_wake = self.fmodel.get_farm_AEP()
            wake_losses = 100 * (aep_no_wake - aep) / aep_no_wake

            # Mostrar resultados textuales
            self.result_text.configure(state="normal")
            self.result_text.delete("1.0", "end")
            self.result_text.insert("end", "✅ Simulación completada\n\n")
            self.result_text.insert("end", f"Potencia total: {farm_power} kW\n")
            self.result_text.insert("end", f"Potencia por turbina: {turbine_powers}\n\n")
            self.result_text.insert("end", f"AEP estimado: {aep/1e9:.3f} GWh/año\n")
            self.result_text.insert("end", f"AEP sin pérdidas por estela: {aep_no_wake/1e9:.3f} GWh/año\n")
            self.result_text.insert("end", f"Pérdidas por estela: {wake_losses:.2f}%\n")
            self.result_text.configure(state="disabled")

            # Generar visualizaciones en el área scrollable
            self.visualizar_layout(layout)
            self.visualizar_flujo()

        except Exception as e:
            CTkMessagebox(title="❌ Error de simulación", message=str(e))

    def visualizar_layout(self, layout):
        """Muestra el layout de las turbinas dentro del área scrollable"""
        fig, ax = plt.subplots(figsize=(7, 3))
        layoutviz.plot_turbine_points(self.fmodel, ax=ax)
        ax.set_title("Distribución espacial de turbinas")

        layout_canvas = FigureCanvasTkAgg(fig, master=self.frame_graficas)
        layout_canvas.draw()
        layout_canvas.get_tk_widget().pack(fill="both", expand=True, pady=10)

    def visualizar_flujo(self):
        """Muestra el campo de flujo dentro del área scrollable"""
        horizontal_plane = self.fmodel.calculate_horizontal_plane(
            x_resolution=150,
            y_resolution=75,
            height=90.0,
        )

        fig, ax = plt.subplots(figsize=(7, 5))  # más grande
        visualize_cut_plane(horizontal_plane, ax=ax, label_contours=False,
                            title="Campo de flujo a altura del buje")
        layoutviz.plot_turbine_rotors(self.fmodel, ax=ax)
        ax.set_xlabel("x [m]")
        ax.set_ylabel("y [m]")

        flow_canvas = FigureCanvasTkAgg(fig, master=self.frame_graficas)
        flow_canvas.draw()
        flow_canvas.get_tk_widget().pack(fill="both", expand=True, pady=10)

