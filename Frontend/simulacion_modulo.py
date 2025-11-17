from CTkMessagebox import CTkMessagebox
import numpy as np
from floris import FlorisModel
import floris.layout_visualization as layoutviz
from floris.flow_visualization import visualize_cut_plane
import matplotlib.pyplot as plt
from matplotlib.backends.backend_tkagg import FigureCanvasTkAgg
import tkinter as tk
import threading
import customtkinter as ctk
import warnings
warnings.filterwarnings("ignore")
from floris import WindRose

class SimulacionManager:
    def __init__(self, parent, tab_simulacion):
        self.parent = parent
        self.tab_simulacion = tab_simulacion
        self.fmodel = FlorisModel(
            r"C:\Users\DELL\Desktop\Cosas universidad sexto semestre\pf_electrica\Frontend\gch.yaml"
        )

        self.layout_canvas = None
        self.flow_canvas = None
        self.simulando = False  # Para evitar ejecuciones simultáneas

        self.crear_interfaz()

    def crear_interfaz(self):


        self.frame_principal = ctk.CTkFrame(self.tab_simulacion)
        self.frame_principal.pack(fill="both", expand=True, padx=10, pady=10)

        # Panel izquierdo
        self.frame_izquierdo = ctk.CTkFrame(self.frame_principal, width=320)
        self.frame_izquierdo.pack(side="left", fill="y", padx=10, pady=10)

        # Contenedor de resultados (scrollable)
        self.scroll_resultados = ctk.CTkScrollableFrame(self.frame_izquierdo, width=300)
        self.scroll_resultados.pack(fill="both", expand=True, pady=10)

        # Label de estado
        self.label_estado = ctk.CTkLabel(self.frame_izquierdo, text="", text_color="orange")
        self.label_estado.pack(pady=(5, 0))

        # Botón ejecutar
        self.boton_simular = ctk.CTkButton(
            self.frame_izquierdo,
            text="▶️ Ejecutar Simulación",
            fg_color="#2fa86f",
            command=self.ejecutar_simulacion
        )
        self.boton_simular.pack(pady=15)

        # Panel derecho con scroll para gráficas
        self.frame_derecho = ctk.CTkFrame(self.frame_principal)
        self.frame_derecho.pack(side="right", fill="both", expand=True, padx=10, pady=10)

        self.canvas_derecho = tk.Canvas(self.frame_derecho, bg="#1E1E1E", highlightthickness=0)
        self.scrollbar_y = tk.Scrollbar(self.frame_derecho, orient="vertical", command=self.canvas_derecho.yview)
        self.frame_graficas = tk.Frame(self.canvas_derecho, bg="#1E1E1E")

        self.frame_graficas.bind(
            "<Configure>",
            lambda e: self.canvas_derecho.configure(scrollregion=self.canvas_derecho.bbox("all"))
        )
        self.canvas_derecho.create_window((0, 0), window=self.frame_graficas, anchor="nw")
        self.canvas_derecho.configure(yscrollcommand=self.scrollbar_y.set)

        self.canvas_derecho.pack(side="left", fill="both", expand=True)
        self.scrollbar_y.pack(side="right", fill="y")


    # ===========================================================
    # ==== Ejecución en hilo separado ====
    # ===========================================================
    def ejecutar_simulacion(self):
        if self.simulando:
            CTkMessagebox(title="⚙️ En curso", message="La simulación ya está ejecutándose.")
            return

        import time, psutil, os

        if not hasattr(self.parent, "time_series"):
            CTkMessagebox(title="⚠️ Faltan datos NASA", message="Descarga los datos primero.")
            return

        layout = (self.parent.layout.layout_x, self.parent.layout.layout_y)
        if not self.parent.layout.layout_confirmado:
            CTkMessagebox(title="⚠️ Layout no confirmado", message="Confirma el layout primero.")
            return

        # Mostrar estado
        self.label_estado.configure(text="⏳ Simulando... Por favor espere.", text_color="orange")
        self.simulando = True
        self.boton_simular.configure(state="disabled")

        # Lanzar la simulación en otro hilo
        hilo = threading.Thread(target=self._simulacion_worker, args=(layout,))
        hilo.start()

    # ===========================================================
    # ==== Lógica pesada de simulación ====
    # ===========================================================
    def _simulacion_worker(self, layout):
        import time, psutil, os, json
        from pathlib import Path
        from floris.turbine_library import build_cosine_loss_turbine_dict

        try:
            start_time = time.time()
            process = psutil.Process(os.getpid())
            mem_before = process.memory_info().rss / (1024 ** 2)

            # === Configurar turbina ===
            if getattr(self.parent, "tipo_turbina", "Referencia") == "Referencia":
                self.fmodel.set(turbine_type=[self.parent.turbina_interna])
            else:
                json_path = Path(__file__).parent / "turbines" / "turbinas_reales.json"
                with open(json_path, "r") as f:
                    turbinas_reales = json.load(f)
                data = turbinas_reales[self.parent.turbina_interna]
                power_curve = np.array(data["power_curve"]) * [1, 1000]
                ct_curve = np.array(data["ct_curve"])
                wind_speeds = power_curve[:, 0]
                power_coeffs = (
                    power_curve[:, 1] /
                    (0.5 * data["ref_air_density"] * np.pi *
                     (data["rotor_diameter"] / 2) ** 2 * wind_speeds ** 3)
                )
                turbine_data_dict = {
                    "wind_speed": wind_speeds.tolist(),
                    "power_coefficient": power_coeffs.tolist(),
                    "thrust_coefficient": ct_curve[:, 1].tolist(),
                }
                turbine_dict = build_cosine_loss_turbine_dict(
                    turbine_data_dict,
                    "V164_9_5MW",
                    file_name=None,
                    generator_efficiency=data["generator_efficiency"],
                    hub_height=data["hub_height"],
                    cosine_loss_exponent_yaw=data["cosine_loss_exponent_yaw"],
                    cosine_loss_exponent_tilt=data["cosine_loss_exponent_tilt"],
                    rotor_diameter=data["rotor_diameter"],
                    TSR=data["TSR"],
                    ref_air_density=data["ref_air_density"],
                    ref_tilt=data["ref_tilt"],
                )
                self.fmodel.set(turbine_type=[turbine_dict])

            # === Layout y viento ===
            self.fmodel.set(layout_x=layout[0], layout_y=layout[1])
            self.fmodel.set(wind_data=self.parent.time_series)

            # === Simulación ===
            self.fmodel.run()
            turbine_powers = self.fmodel.get_turbine_powers() / 1000.0
            farm_power = self.fmodel.get_farm_power() / 1000.0
            aep = self.fmodel.get_farm_AEP()
            self.fmodel.run_no_wake()
            aep_no_wake = self.fmodel.get_farm_AEP()

            # === Cálculos finales ===
            tp_arr = np.asarray(turbine_powers)
            mean_powers = np.mean(tp_arr, axis=0) if tp_arr.ndim >= 2 else np.atleast_1d(tp_arr)
            farm_power_mean = float(np.mean(np.asarray(farm_power)))
            aep_scalar_Wh = float(np.mean(np.asarray(aep)))
            aep_no_wake_scalar_Wh = float(np.mean(np.asarray(aep_no_wake)))
            wake_losses_scalar = (
                100.0 * (aep_no_wake_scalar_Wh - aep_scalar_Wh) / aep_no_wake_scalar_Wh
                if aep_no_wake_scalar_Wh > 0 else 0.0
            )

            pot_nominal = float(getattr(self.parent, "potencia_nominal_turbina_mw", 5.0))
            num_turbinas = len(layout[0])
            E_max_GWh = pot_nominal * num_turbinas * 8760.0 / 1000.0
            E_real_GWh = aep_scalar_Wh / 1e9
            CF_pct = 100.0 * E_real_GWh / E_max_GWh if E_max_GWh > 0 else 0.0
            mem_after = process.memory_info().rss / (1024 ** 2)
            elapsed_time = time.time() - start_time
            mem_used = mem_after - mem_before

            # Actualizar UI desde el hilo principal
            self.parent.after(0, lambda: self._mostrar_resultados(
                layout, mean_powers, farm_power_mean, E_real_GWh,
                aep_no_wake_scalar_Wh, wake_losses_scalar, E_max_GWh,
                CF_pct, elapsed_time, mem_used
            ))

        except Exception as e:
            self.parent.after(0, lambda: CTkMessagebox(title="❌ Error de simulación", message=str(e)))

        finally:
            self.parent.after(0, self._finalizar_simulacion)

    # ===========================================================
    # ==== Mostrar resultados ====
    # ===========================================================
    def _mostrar_resultados(self, layout, mean_powers, farm_power_mean,
                            E_real_GWh, aep_no_wake_scalar_Wh, wake_losses_scalar,
                            E_max_GWh, CF_pct, elapsed_time, mem_used):

        # Limpiar resultados anteriores
        for widget in self.scroll_resultados.winfo_children():
            widget.destroy()

        def crear_tarjeta(titulo, valor, color="#2fa86f", icono="⚡", destacada=False):
            # Estilo especial si la tarjeta es destacada
            if destacada:
                fg_color = "#333333"
                font_titulo = ctk.CTkFont(size=16, weight="bold")
                font_valor = ctk.CTkFont(size=18, weight="bold")
                padding_y = 10
                border = 3
            else:
                fg_color = "#222222"
                font_titulo = ctk.CTkFont(size=13, weight="bold")
                font_valor = ctk.CTkFont(size=14)
                padding_y = 5
                border = 0

            card = ctk.CTkFrame(
                self.scroll_resultados,
                fg_color=fg_color,
                corner_radius=12,
                border_width=border,
                border_color=color
            )
            card.pack(fill="x", pady=padding_y, padx=8)

            ctk.CTkLabel(
                card, text=f"{icono} {titulo}",
                font=font_titulo
            ).pack(anchor="w", padx=12, pady=(5, 0))

            ctk.CTkLabel(
                card, text=valor,
                font=font_valor,
                text_color=color
            ).pack(anchor="w", padx=18, pady=(0, 10))

            return card


        # --- Ejemplo de uso ---
        pot_nominal = getattr(self.parent, "potencia_nominal_turbina_mw", 5.0)
        num_turbinas = len(layout[0])
        crear_tarjeta("AEP estimado", f"{E_real_GWh:.3f} GWh/año", color="#00b4d8", icono="📈", destacada=True)
        crear_tarjeta("Pérdidas por estela", f"{wake_losses_scalar:.2f}%", color="#ffb703", icono="🌫️", destacada=True)
        crear_tarjeta("Turbina seleccionada", self.parent.turbina_interna, icono="🌪️")
        crear_tarjeta("Potencia nominal", f"{pot_nominal:.1f} MW", icono="⚙️")
        crear_tarjeta("Número de turbinas", str(num_turbinas), icono="🌀")
        crear_tarjeta("Potencia total promedio", f"{farm_power_mean:.1f} kW", color="#2fa86f", icono="⚡")
        crear_tarjeta("Energía máxima teórica", f"{E_max_GWh:.2f} GWh/año", color="#90be6d", icono="💡")
        crear_tarjeta("Factor de capacidad (CF)", f"{CF_pct:.2f}%", color="#8ecae6", icono="📊")


        # Sección final: rendimiento y métricas
        ctk.CTkLabel(self.scroll_resultados, text="Resumen de desempeño", font=ctk.CTkFont(size=15, weight="bold")).pack(pady=(10, 5))
        if CF_pct < 30:
            color, texto = "orange", "⚠️ CF bajo — recurso eólico limitado."
        elif CF_pct < 45:
            color, texto = "#a3be8c", "✅ CF moderado — sitio típico."
        else:
            color, texto = "#00ff88", "🌊 CF alto — excelente recurso eólico."
        ctk.CTkLabel(self.scroll_resultados, text=texto, text_color=color).pack(pady=(0, 10))

        crear_tarjeta("Tiempo de simulación", f"{elapsed_time:.2f} s", color="#d9d9d9", icono="⏱️")
        crear_tarjeta("Memoria usada", f"{mem_used:.2f} MB", color="#d9d9d9", icono="💾")

        # Visualizaciones
        self.visualizar_layout(layout)
        self.visualizar_flujo()
        self.visualizar_time_series()
        self.visualizar_wind_rose_floris()

        self.label_estado.configure(text="✅ Simulación completada.", text_color="green")


    def _finalizar_simulacion(self):
        self.simulando = False
        self.boton_simular.configure(state="normal")
        self.label_estado.configure(text="✅ Simulación completada.", text_color="green")

    # ===========================================================
    # ==== Visualizaciones ====
    # ===========================================================
    def visualizar_layout(self, layout):
        fig, ax = plt.subplots(figsize=(7, 3))
        layoutviz.plot_turbine_points(self.fmodel, ax=ax)

        # --- Personalización del gráfico ---
        ax.set_title("Distribución espacial de turbinas", fontsize=12, fontweight="bold")
        ax.set_xlabel("X [m]", fontsize=10)
        ax.set_ylabel("Y [m]", fontsize=10)
        ax.grid(True, linestyle="--", alpha=0.5)
        ax.set_facecolor("#f9f9f9")

        # 🔧 Ajuste de márgenes para que no se corte el texto del eje X
        fig.tight_layout(pad=2)
        fig.subplots_adjust(bottom=0.2)  # deja más espacio bajo el eje X

        # --- Mostrar en el panel ---
        layout_canvas = FigureCanvasTkAgg(fig, master=self.frame_graficas)
        layout_canvas.draw()
        layout_canvas.get_tk_widget().pack(fill="both", expand=True, pady=10)



    def visualizar_flujo(self):
        horizontal_plane = self.fmodel.calculate_horizontal_plane(
            x_resolution=150, y_resolution=75, height=90.0)
        fig, ax = plt.subplots(figsize=(7, 5))
        visualize_cut_plane(horizontal_plane, ax=ax, label_contours=False,
                            title="Campo de flujo a altura del buje")
        layoutviz.plot_turbine_rotors(self.fmodel, ax=ax)
        ax.set_xlabel("X [m]")
        ax.set_ylabel("Y [m]")
        flow_canvas = FigureCanvasTkAgg(fig, master=self.frame_graficas)
        flow_canvas.draw()
        flow_canvas.get_tk_widget().pack(fill="both", expand=True, pady=10)
    def visualizar_time_series(self):
            ts = self.parent.time_series
            wind_directions = np.array(ts.wind_directions)
            wind_speeds = np.array(ts.wind_speeds)
            turbulence_intensities = np.array(ts.turbulence_intensities)

            fig, axes = plt.subplots(3, 1, figsize=(7, 6), sharex=True)

            # Título general
            fig.suptitle("Series Temporales del Recurso Eólico", fontsize=20)

            # Gráficas
            axes[0].plot(wind_directions, color='tab:blue')
            axes[0].set_ylabel("Dirección [°]", fontsize=20)

            axes[1].plot(wind_speeds, color='tab:green')
            axes[1].set_ylabel("Velocidad [m/s]", fontsize=20)

            axes[2].plot(turbulence_intensities, color='tab:orange')
            axes[2].set_ylabel("TI", fontsize=20)
            axes[2].set_xlabel("Horas del año [h]", fontsize=20)

            # Aplicar font size a ticks y grid
            for ax in axes:
                ax.tick_params(axis='both', labelsize=20)
                ax.grid(True, linestyle='--', alpha=0.5)

            ts_canvas = FigureCanvasTkAgg(fig, master=self.frame_graficas)
            ts_canvas.draw()
            ts_canvas.get_tk_widget().pack(fill="both", expand=True, pady=10)


    from floris import WindRose
    import numpy as np
    import matplotlib.pyplot as plt
    from matplotlib.backends.backend_tkagg import FigureCanvasTkAgg

    def visualizar_wind_rose_floris(self):
        ts = self.parent.time_series
        wind_directions = np.array(ts.wind_directions)
        wind_speeds = np.array(ts.wind_speeds)
        turbulence_intensities = np.array(ts.turbulence_intensities)

        # --- 1. Discretizar datos ---
        dir_bins = np.arange(0, 360, 10)  # cada 10°
        spd_bins = np.arange(0, np.ceil(np.max(wind_speeds)) + 1, 1)  # cada 1 m/s

        freq_table, _, _ = np.histogram2d(
            wind_directions,
            wind_speeds,
            bins=[dir_bins, spd_bins],
            density=True
        )
        freq_table = freq_table / np.sum(freq_table)
        dir_table = 0.5 * (dir_bins[:-1] + dir_bins[1:])
        spd_table = 0.5 * (spd_bins[:-1] + spd_bins[1:])

        # --- 2. Crear objeto WindRose ---
        wind_rose = WindRose(
            wind_directions=dir_table,
            wind_speeds=spd_table,
            ti_table=np.mean(turbulence_intensities),
            freq_table=freq_table
        )

        # --- 3. Graficar ---
        fig = plt.figure(figsize=(6, 6))
        ax = fig.add_subplot(111, projection="polar")
        wind_rose.plot(ax=ax)

        ax.set_title("Rosa de Vientos - Distribución del Recurso Eólico", pad=20)
        ax.grid(True, linestyle='--', alpha=0.5)

        # --- 4. Agregar ángulos junto con puntos cardinales ---
        ax.set_thetagrids(
            np.arange(0, 360, 45),
            labels=['0° N', '45° NE', '90° E', '135° SE', '180° S', '225° SW', '270° W', '315° NW']
        )

        # --- 5. Eliminar los valores numéricos radiales (frecuencias) ---
        ax.set_yticklabels([])  # Oculta las etiquetas dentro del círculo

        # --- 6. Mostrar en Tkinter ---
        windrose_canvas = FigureCanvasTkAgg(fig, master=self.frame_graficas)
        windrose_canvas.draw()
        windrose_canvas.get_tk_widget().pack(fill="both", expand=True, pady=10)
