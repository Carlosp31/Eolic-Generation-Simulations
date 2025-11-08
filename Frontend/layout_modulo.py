import customtkinter as ctk
from CTkMessagebox import CTkMessagebox
from tkinter import filedialog
import pandas as pd


class LayoutManager:
    def __init__(self, parent, tab_plano):
        self.parent = parent
        self.tab_plano = tab_plano
        self.layout_x, self.layout_y = [], []
        self.layout_confirmado = False
        self.zoom_factor = 1.0
        self.center_x = 0
        self.center_y = 0
        self.tooltip = None  # referencia al texto flotante

        # Variables para arrastre
        self.dragging = False
        self.drag_start_x = 0
        self.drag_start_y = 0
        self.drag_threshold = 5  # píxeles para diferenciar clic corto de arrastre
        self.moved_during_drag = False

        self.crear_interfaz()
        self.canvas.bind("<Motion>", self.mostrar_tooltip_turbina)

    def crear_interfaz(self):
        # --- Sección izquierda: mapa o plano ---
        canvas_frame = ctk.CTkFrame(self.tab_plano)
        canvas_frame.pack(side="left", expand=True, fill="both", padx=10, pady=10)

        self.canvas = ctk.CTkCanvas(canvas_frame, bg="#1e1e1e", highlightthickness=0)
        self.canvas.pack(expand=True, fill="both")

        # Eventos
        self.canvas.bind("<Configure>", self.redibujar_todo)
        self.canvas.bind("<ButtonPress-1>", self.iniciar_arrastre)
        self.canvas.bind("<B1-Motion>", self.mover_plano)
        self.canvas.bind("<ButtonRelease-1>", self.finalizar_click_o_arrastre)
        self.canvas.bind("<MouseWheel>", self.zoom_mouse)

        # --- Sección derecha: controles ---
        right_frame = ctk.CTkFrame(self.tab_plano)
        right_frame.pack(side="right", fill="y", padx=10, pady=10)

        self.coord_list = ctk.CTkTextbox(right_frame, width=200, height=250)
        self.coord_list.pack(fill="y", pady=(0, 10))
        self.coord_list.insert("end", "Coordenadas de turbinas:\n")

        ctk.CTkButton(
            right_frame, text="🗑 Borrar última turbina",
            fg_color="#c62828", command=self.borrar_ultima_turbina
        ).pack(pady=(0, 10))

        ctk.CTkButton(
            right_frame, text="♻️ Borrar todo",
            fg_color="#6d4c41", command=self.borrar_todas_turbinas
        ).pack(pady=(0, 10))

        manual_frame = ctk.CTkFrame(right_frame)
        manual_frame.pack(pady=10)

        ctk.CTkLabel(manual_frame, text="X:").grid(row=0, column=0)
        self.x_entry = ctk.CTkEntry(manual_frame, width=70)
        self.x_entry.grid(row=0, column=1)
        ctk.CTkLabel(manual_frame, text="Y:").grid(row=1, column=0)
        self.y_entry = ctk.CTkEntry(manual_frame, width=70)
        self.y_entry.grid(row=1, column=1)

        ctk.CTkButton(
            manual_frame, text="➕ Agregar", command=self.agregar_turbina_manual
        ).grid(row=2, column=0, columnspan=2, pady=10)

        ctk.CTkButton(
            right_frame, text="📂 Cargar coordenadas desde Excel",
            fg_color="#1e88e5", command=self.cargar_desde_excel
        ).pack(pady=10)

        ctk.CTkButton(
            right_frame, text="✅ Confirmar Layout",
            fg_color="#2fa86f", command=self.confirmar_layout
        ).pack(pady=10)

    # --------------------------
    # --- FUNCIONES PRINCIPALES
    # --------------------------

    def iniciar_arrastre(self, event):
        """Inicia el arrastre o posible clic."""
        self.dragging = True
        self.drag_start_x = event.x
        self.drag_start_y = event.y
        self.moved_during_drag = False

    def mover_plano(self, event):
        """Permite mover el plano mientras se arrastra."""
        if not self.dragging:
            return

        dx = event.x - self.drag_start_x
        dy = event.y - self.drag_start_y

        if abs(dx) > self.drag_threshold or abs(dy) > self.drag_threshold:
            self.moved_during_drag = True

        self.center_x -= dx / self.zoom_factor
        self.center_y += dy / self.zoom_factor

        self.drag_start_x = event.x
        self.drag_start_y = event.y

        self.redibujar_todo()

    def finalizar_click_o_arrastre(self, event):
        """Distingue entre clic y arrastre al soltar el botón."""
        if not self.moved_during_drag:
            # Fue un clic: agregar turbina
            self.agregar_turbina_click(event)
        self.dragging = False

    def world_to_canvas(self, x, y):
        """Transforma coordenadas reales al sistema del canvas (centro en pantalla)"""
        w, h = self.canvas.winfo_width(), self.canvas.winfo_height()
        canvas_x = (x - self.center_x) * self.zoom_factor + w / 2
        canvas_y = h / 2 - (y - self.center_y) * self.zoom_factor
        return canvas_x, canvas_y

    def dibujar_grid(self):
        """Dibuja el grid con etiquetas numéricas adaptativas y ejes principales marcados"""
        self.canvas.delete("grid_line")
        self.canvas.delete("grid_label")

        w, h = self.canvas.winfo_width(), self.canvas.winfo_height()
        cx, cy = w / 2, h / 2

        # --- Ajuste dinámico del paso del grid según zoom ---
        base_step = 100
        step_world = base_step
        if self.zoom_factor < 0.3:
            step_world = 1000
        elif self.zoom_factor < 0.6:
            step_world = 500
        elif self.zoom_factor < 1.0:
            step_world = 200
        elif self.zoom_factor > 3.0:
            step_world = 50
        elif self.zoom_factor > 6.0:
            step_world = 25

        # --- Control adaptativo de etiquetas ---
        num_turbinas = len(self.layout_x)
        etiqueta_cada = 1

        # Cuantas más turbinas o más alejado el zoom, menos etiquetas
        if num_turbinas > 40 or self.zoom_factor < 0.5:
            etiqueta_cada = 5
        elif num_turbinas > 80 or self.zoom_factor < 0.3:
            etiqueta_cada = 10
        elif num_turbinas > 120 or self.zoom_factor < 0.15:
            etiqueta_cada = 20

        max_lines = 200

        # --- Líneas verticales (X) ---
        x_val = self.center_x - (cx / self.zoom_factor)
        count = 0
        while x_val <= self.center_x + (cx / self.zoom_factor) and count < max_lines:
            x_canvas = (x_val - self.center_x) * self.zoom_factor + cx
            self.canvas.create_line(x_canvas, 0, x_canvas, h, fill="#333", width=1, tags="grid_line")

            if abs(x_val) > 1e-6 and count % etiqueta_cada == 0:
                self.canvas.create_text(
                    x_canvas + 2, cy + 5,
                    text=f"{x_val:.0f}", anchor="nw",
                    fill="#888", font=("Arial", 8), tags="grid_label"
                )
            x_val += step_world
            count += 1

        # --- Líneas horizontales (Y) ---
        y_val = self.center_y + (cy / self.zoom_factor)
        count = 0
        while y_val >= self.center_y - (cy / self.zoom_factor) and count < max_lines:
            y_canvas = cy - (y_val - self.center_y) * self.zoom_factor
            self.canvas.create_line(0, y_canvas, w, y_canvas, fill="#333", width=1, tags="grid_line")

            if abs(y_val) > 1e-6 and count % etiqueta_cada == 0:
                self.canvas.create_text(
                    cx + 5, y_canvas - 10,
                    text=f"{y_val:.0f}", anchor="nw",
                    fill="#888", font=("Arial", 8), tags="grid_label"
                )
            y_val -= step_world
            count += 1

        # --- Ejes ---
        eje_x = cy - (0 - self.center_y) * self.zoom_factor
        eje_y = (0 - self.center_x) * self.zoom_factor + cx
        self.canvas.create_line(0, eje_x, w, eje_x, fill="#00ffff", width=2, tags="grid_line")
        self.canvas.create_line(eje_y, 0, eje_y, h, fill="#00ffff", width=2, tags="grid_line")

        # Etiquetas de ejes
        self.canvas.create_text(w - 50, eje_x - 20, text="x [m]",
                                fill="white", font=("Arial", 10, "bold"), tags="grid_label")
        self.canvas.create_text(eje_y + 25, 25, text="y [m]",
                                fill="white", font=("Arial", 10, "bold"), angle=90, tags="grid_label")


    def agregar_turbina(self, x, y):
        if self.layout_confirmado:
            CTkMessagebox(title="⚠️ Layout bloqueado", message="Ya confirmaste el layout.")
            return
        self.layout_x.append(x)
        self.layout_y.append(y)
        self.coord_list.insert("end", f"({x:.1f}, {y:.1f})\n")
        self.redibujar_todo()

    def agregar_turbina_click(self, event):
        w, h = self.canvas.winfo_width(), self.canvas.winfo_height()
        x = (event.x - w / 2) / self.zoom_factor + self.center_x
        y = (h / 2 - event.y) / self.zoom_factor + self.center_y
        self.agregar_turbina(x, y)

    def mostrar_tooltip_turbina(self, event):
        if self.tooltip:
            self.canvas.delete(self.tooltip)
            self.tooltip = None

        for x, y in zip(self.layout_x, self.layout_y):
            cx, cy = self.world_to_canvas(x, y)
            if ((event.x - cx) ** 2 + (event.y - cy) ** 2) ** 0.5 <= 8:
                texto = f"({x:.1f}, {y:.1f})"
                self.tooltip = self.canvas.create_text(
                    event.x + 10, event.y - 10, text=texto, fill="white",
                    font=("Arial", 10, "bold"), tags="tooltip", anchor="w"
                )
                break

    def agregar_turbina_manual(self):
        try:
            x, y = float(self.x_entry.get()), float(self.y_entry.get())
            self.agregar_turbina(x, y)
        except ValueError:
            CTkMessagebox(title="⚠️ Error", message="Valores numéricos inválidos")

    def redibujar_todo(self, event=None):
        self.canvas.delete("all")
        self.dibujar_grid()
        for x, y in zip(self.layout_x, self.layout_y):
            cx, cy = self.world_to_canvas(x, y)
            self.canvas.create_oval(cx - 5, cy - 5, cx + 5, cy + 5, fill="lime", outline="", tags="turbina")

    def zoom_mouse(self, event):
        if event.delta > 0:
            self.zoom_factor *= 1.1
        else:
            self.zoom_factor /= 1.1
        self.zoom_factor = max(0.05, min(self.zoom_factor, 10))
        self.redibujar_todo()

    def borrar_ultima_turbina(self):
        if self.layout_x:
            self.layout_x.pop()
            self.layout_y.pop()
            self.actualizar_lista()
            self.redibujar_todo()

    def borrar_todas_turbinas(self):
        self.layout_x.clear()
        self.layout_y.clear()
        self.actualizar_lista()
        self.redibujar_todo()

    def actualizar_lista(self):
        self.coord_list.delete("1.0", "end")
        self.coord_list.insert("end", "Coordenadas de turbinas:\n")
        for x, y in zip(self.layout_x, self.layout_y):
            self.coord_list.insert("end", f"({x:.1f}, {y:.1f})\n")

    def autoajustar_vista(self):
        if not self.layout_x:
            return
        min_x, max_x = min(self.layout_x), max(self.layout_x)
        min_y, max_y = min(self.layout_y), max(self.layout_y)
        self.center_x = (min_x + max_x) / 2
        self.center_y = (min_y + max_y) / 2
        rango_x = max_x - min_x
        rango_y = max_y - min_y
        w, h = self.canvas.winfo_width(), self.canvas.winfo_height()
        if rango_x == 0 or rango_y == 0:
            self.zoom_factor = 1.0
        else:
            self.zoom_factor = min(w / (rango_x * 1.4), h / (rango_y * 1.4))
        self.redibujar_todo()

    def cargar_desde_excel(self):
        ruta = filedialog.askopenfilename(
            title="Seleccionar archivo de coordenadas",
            filetypes=[("Archivos Excel o CSV", "*.xlsx *.csv")]
        )
        if not ruta:
            return
        try:
            df = pd.read_csv(ruta) if ruta.endswith(".csv") else pd.read_excel(ruta)
            col_x = next(c for c in df.columns if "x" in c.lower())
            col_y = next(c for c in df.columns if "y" in c.lower())
            for _, fila in df.iterrows():
                x, y = fila[col_x], fila[col_y]
                if pd.notna(x) and pd.notna(y):
                    self.layout_x.append(float(x))
                    self.layout_y.append(float(y))
            self.autoajustar_vista()
            self.actualizar_lista()
            CTkMessagebox(title="✅ Éxito", message=f"Se cargaron {len(self.layout_x)} coordenadas desde el archivo.")
        except Exception as e:
            CTkMessagebox(title="⚠️ Error al leer archivo", message=str(e))

    def confirmar_layout(self):
        if not self.layout_x:
            CTkMessagebox(title="⚠️ Sin turbinas", message="Agrega al menos una turbina.")
            return
        self.layout_confirmado = True
        CTkMessagebox(title="✅ Layout confirmado", message=f"Se definieron {len(self.layout_x)} turbinas.")
