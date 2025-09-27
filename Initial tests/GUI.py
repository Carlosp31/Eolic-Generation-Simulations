import tkinter as tk
from tkinter import ttk, messagebox
import matplotlib.pyplot as plt
from matplotlib.backends.backend_tkagg import FigureCanvasTkAgg

# Importar PyWake
from py_wake.examples.data.hornsrev1 import Hornsrev1Site, V80
from py_wake import NOJ
import numpy as np

class PyWakeGUI:
    def __init__(self, root):
        self.root = root
        self.root.title("Simulación de Parque Eólico con PyWake")
        self.root.geometry("800x600")

        # ---- Parámetros de entrada ----
        frame_inputs = ttk.LabelFrame(root, text="Parámetros de Simulación")
        frame_inputs.pack(fill="x", padx=10, pady=5)

        # Número de turbinas
        ttk.Label(frame_inputs, text="Número de turbinas:").grid(row=0, column=0, padx=5, pady=5)
        self.num_turbinas = tk.IntVar(value=4)
        ttk.Entry(frame_inputs, textvariable=self.num_turbinas, width=10).grid(row=0, column=1)

        # Separación entre turbinas
        ttk.Label(frame_inputs, text="Separación (m):").grid(row=1, column=0, padx=5, pady=5)
        self.separacion = tk.DoubleVar(value=560)
        ttk.Entry(frame_inputs, textvariable=self.separacion, width=10).grid(row=1, column=1)

        # Botón de simulación
        ttk.Button(frame_inputs, text="Ejecutar Simulación", command=self.run_simulation).grid(row=2, column=0, columnspan=2, pady=10)

        # ---- Resultados ----
        frame_results = ttk.LabelFrame(root, text="Resultados")
        frame_results.pack(fill="both", expand=True, padx=10, pady=5)

        self.text_results = tk.Text(frame_results, height=10)
        self.text_results.pack(fill="x", padx=5, pady=5)

        # Frame para gráficos
        self.frame_plot = ttk.Frame(frame_results)
        self.frame_plot.pack(fill="both", expand=True, padx=5, pady=5)

    def run_simulation(self):
        try:
            n_turbinas = self.num_turbinas.get()
            dx = self.separacion.get()

            # ---- Setup del sitio y turbina ----
            site = Hornsrev1Site()
            windTurbine = V80()

            # Layout lineal simple
            x = np.arange(0, n_turbinas) * dx
            y = np.zeros(n_turbinas)

            # Modelo NOJ
            wake_model = NOJ(site, windTurbine)

            sim_res = wake_model(x, y)
            aep = sim_res.aep().sum() / 1e6  # GWh

            # Mostrar resultados
            self.text_results.delete(1.0, tk.END)
            self.text_results.insert(tk.END, f"Producción Anual Estimada: {aep:.2f} GWh\n")

            # ---- Gráfico ----
            fig, ax = plt.subplots(figsize=(5, 4))
            sim_res.flow_map(wd=270).plot_wake_map(ax=ax, levels=50)
            ax.set_title("Mapa de estela (270°)")

            # Limpiar gráficos previos
            for widget in self.frame_plot.winfo_children():
                widget.destroy()

            canvas = FigureCanvasTkAgg(fig, master=self.frame_plot)
            canvas.draw()
            canvas.get_tk_widget().pack(fill="both", expand=True)

        except Exception as e:
            messagebox.showerror("Error", str(e))


if __name__ == "__main__":
    root = tk.Tk()
    app = PyWakeGUI(root)
    root.mainloop()
