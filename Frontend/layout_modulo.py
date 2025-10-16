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
        self.crear_interfaz()

    def crear_interfaz(self):
        # --- Sección izquierda: mapa o plano ---
        canvas_frame = ctk.CTkFrame(self.tab_plano)
        canvas_frame.pack(side="left", expand=True, fill="both", padx=10, pady=10)
        self.canvas = ctk.CTkCanvas(canvas_frame, bg="#1e1e1e", highlightthickness=0)
        self.canvas.pack(expand=True, fill="both")

        # Eventos de interacción
        self.canvas.bind("<Configure>", self.dibujar_grid)
        self.canvas.bind("<Button-1>", self.agregar_turbina_click)
        self.canvas.bind("<MouseWheel>", self.zoom_mouse)  # Zoom con rueda del ratón

        # --- Sección derecha: controles ---
        right_frame = ctk.CTkFrame(self.tab_plano)
        right_frame.pack(side="right", fill="y", padx=10, pady=10)

        # Texto con coordenadas
        self.coord_list = ctk.CTkTextbox(right_frame, width=200, height=250)
        self.coord_list.pack(fill="y", pady=(0, 10))
        self.coord_list.insert("end", "Coordenadas de turbinas:\n")

        # Hacer editable (antes estaba bloqueado)
        self.coord_list.configure(state="normal")

        # Botón borrar última turbina
        ctk.CTkButton(
            right_frame,
            text="🗑 Borrar última turbina",
            fg_color="#c62828",
            command=self.borrar_ultima_turbina
        ).pack(pady=(0, 10))

        # Botón borrar todas las turbinas
        ctk.CTkButton(
            right_frame,
            text="♻️ Borrar todo",
            fg_color="#6d4c41",
            command=self.borrar_todas_turbinas
        ).pack(pady=(0, 10))

        # Entrada manual
        manual_frame = ctk.CTkFrame(right_frame)
        manual_frame.pack(pady=10)
        ctk.CTkLabel(manual_frame, text="X:").grid(row=0, column=0)
        self.x_entry = ctk.CTkEntry(manual_frame, width=70)
        self.x_entry.grid(row=0, column=1)
        ctk.CTkLabel(manual_frame, text="Y:").grid(row=1, column=0)
        self.y_entry = ctk.CTkEntry(manual_frame, width=70)
        self.y_entry.grid(row=1, column=1)
        ctk.CTkButton(manual_frame, text="➕ Agregar", command=self.agregar_turbina_manual).grid(
            row=2, column=0, columnspan=2, pady=10
        )

        # Cargar desde Excel
        ctk.CTkButton(
            right_frame,
            text="📂 Cargar coordenadas desde Excel",
            fg_color="#1e88e5",
            command=self.cargar_desde_excel
        ).pack(pady=10)

        # Confirmar layout
        ctk.CTkButton(
            right_frame, text="✅ Confirmar Layout",
            fg_color="#2fa86f", command=self.confirmar_layout
        ).pack(pady=10)

    def dibujar_grid(self, event=None):
        """Dibuja el grid con líneas y etiquetas numéricas en X e Y"""
        self.canvas.delete("grid_line")
        self.canvas.delete("grid_label")

        w, h = self.canvas.winfo_width(), self.canvas.winfo_height()
        step = 50 * self.zoom_factor  # Tamaño de cada celda

        # --- Líneas verticales y etiquetas X ---
        for i in range(0, int(w), int(step)):
            self.canvas.create_line(i, 0, i, h, fill="#333", tags="grid_line")
            label_x = i / self.zoom_factor
            # Evitar dibujar el 0 para no superponerlo con el del eje Y
            if label_x != 0:
                self.canvas.create_text(
                    i + 5, 5,
                    text=f"{label_x:.0f}",
                    anchor="nw",
                    fill="#888",
                    font=("Arial", 8),
                    tags="grid_label"
                )


        # --- Líneas horizontales y etiquetas Y ---
        for j in range(0, int(h), int(step)):
            self.canvas.create_line(0, j, w, j, fill="#333", tags="grid_line")
            label_y = j / self.zoom_factor
            self.canvas.create_text(
                5, j + 5,
                text=f"{label_y:.0f}",
                anchor="nw",
                fill="#888",
                font=("Arial", 8),
                tags="grid_label"
            )


    def agregar_turbina(self, x, y):
        if self.layout_confirmado:
            CTkMessagebox(title="⚠️ Layout bloqueado", message="Ya confirmaste el layout.")
            return
        # Dibujar punto escalado
        scaled_x = x * self.zoom_factor
        scaled_y = y * self.zoom_factor
        self.canvas.create_oval(
            scaled_x - 5, scaled_y - 5, scaled_x + 5, scaled_y + 5,
            fill="lime", outline="", tags="turbina"
        )
        self.layout_x.append(x)
        self.layout_y.append(y)
        self.coord_list.insert("end", f"({x:.1f}, {y:.1f})\n")

    def agregar_turbina_click(self, event):
        # Convertir coordenadas clicadas a coordenadas reales (antes de zoom)
        real_x = event.x / self.zoom_factor
        real_y = event.y / self.zoom_factor
        self.agregar_turbina(real_x, real_y)

    def agregar_turbina_manual(self):
        try:
            x, y = float(self.x_entry.get()), float(self.y_entry.get())
            self.agregar_turbina(x, y)
        except ValueError:
            CTkMessagebox(title="⚠️ Error", message="Valores numéricos inválidos")

    def borrar_ultima_turbina(self):
        """Elimina la última turbina agregada"""
        if not self.layout_x:
            CTkMessagebox(title="⚠️ Nada que borrar", message="No hay turbinas registradas.")
            return
        self.layout_x.pop()
        self.layout_y.pop()
        self.canvas.delete("turbina")
        self.redibujar_turbinas()
        self.actualizar_lista()

    def borrar_todas_turbinas(self):
        """Elimina todas las turbinas"""
        self.layout_x.clear()
        self.layout_y.clear()
        self.canvas.delete("turbina")
        self.actualizar_lista()

    def actualizar_lista(self):
        """Refresca la lista de coordenadas"""
        self.coord_list.delete("1.0", "end")
        self.coord_list.insert("end", "Coordenadas de turbinas:\n")
        for x, y in zip(self.layout_x, self.layout_y):
            self.coord_list.insert("end", f"({x:.1f}, {y:.1f})\n")

    def redibujar_turbinas(self):
        """Redibuja todas las turbinas (útil tras borrar o hacer zoom)"""
        for x, y in zip(self.layout_x, self.layout_y):
            scaled_x = x * self.zoom_factor
            scaled_y = y * self.zoom_factor
            self.canvas.create_oval(
                scaled_x - 5, scaled_y - 5, scaled_x + 5, scaled_y + 5,
                fill="lime", outline="", tags="turbina"
            )

    def zoom_mouse(self, event):
        """Permite hacer zoom con la rueda del ratón"""
        if event.delta > 0:  # Scroll hacia arriba
            self.zoom_factor *= 1.1
        else:  # Scroll hacia abajo
            self.zoom_factor /= 1.1
        self.zoom_factor = max(0.2, min(self.zoom_factor, 5))  # Límites de zoom
        self.canvas.delete("grid_line")
        self.dibujar_grid()
        self.canvas.delete("turbina")
        self.redibujar_turbinas()

    def cargar_desde_excel(self):
        ruta = filedialog.askopenfilename(
            title="Seleccionar archivo de coordenadas",
            filetypes=[("Archivos Excel o CSV", "*.xlsx *.csv")]
        )
        if not ruta:
            return

        try:
            if ruta.endswith(".csv"):
                df = pd.read_csv(ruta)
            else:
                df = pd.read_excel(ruta)

            columnas = [c.lower() for c in df.columns]
            if not any("x" in c for c in columnas) or not any("y" in c for c in columnas):
                CTkMessagebox(title="⚠️ Error", message="El archivo debe tener columnas 'x' y 'y'.")
                return

            col_x = next(c for c in df.columns if "x" in c.lower())
            col_y = next(c for c in df.columns if "y" in c.lower())

            for _, fila in df.iterrows():
                x, y = fila[col_x], fila[col_y]
                if pd.notna(x) and pd.notna(y):
                    self.agregar_turbina(float(x), float(y))

            CTkMessagebox(title="✅ Éxito", message=f"Se cargaron {len(df)} coordenadas desde el archivo.")
        except Exception as e:
            CTkMessagebox(title="⚠️ Error al leer archivo", message=str(e))

    def confirmar_layout(self):
        if not self.layout_x:
            CTkMessagebox(title="⚠️ Sin turbinas", message="Agrega al menos una turbina.")
            return
        self.layout_confirmado = True
        CTkMessagebox(
            title="✅ Layout confirmado",
            message=f"Se definieron {len(self.layout_x)} turbinas."
        )
