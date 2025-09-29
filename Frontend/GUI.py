import customtkinter as ctk

# Configuración global
ctk.set_appearance_mode("dark")  # Modo: "light", "dark", "system"
ctk.set_default_color_theme("green")  # "blue", "green", "dark-blue"

class EolisimApp(ctk.CTk):
    def __init__(self):
        super().__init__()

        # Ventana principal
        self.title("Eolisim - Simulación de Parques Eólicos")
        self.geometry("900x600")

        # Sidebar (menú lateral)
        self.sidebar = ctk.CTkFrame(self, width=200, corner_radius=0)
        self.sidebar.pack(side="left", fill="y")

        # Logo / título
        self.logo = ctk.CTkLabel(self.sidebar, text="🌬️ Eolisim", font=ctk.CTkFont(size=20, weight="bold"))
        self.logo.pack(pady=20)

        # Botones de navegación
        self.btn_parque = ctk.CTkButton(self.sidebar, text="Parque Eólico", command=self.show_parque)
        self.btn_parque.pack(pady=10)

        self.btn_simulacion = ctk.CTkButton(self.sidebar, text="Simulación", command=self.show_simulacion)
        self.btn_simulacion.pack(pady=10)

        self.btn_resultados = ctk.CTkButton(self.sidebar, text="Resultados", command=self.show_resultados)
        self.btn_resultados.pack(pady=10)

        self.btn_config = ctk.CTkButton(self.sidebar, text="Configuración", command=self.show_config)
        self.btn_config.pack(pady=10)

        # Área principal (cambia según sección)
        self.main_area = ctk.CTkFrame(self, corner_radius=10)
        self.main_area.pack(expand=True, fill="both", padx=20, pady=20)

        self.current_frame = None
        self.show_parque()  # Vista inicial

    def clear_main_area(self):
        if self.current_frame is not None:
            self.current_frame.destroy()

    def show_parque(self):
        self.clear_main_area()
        self.current_frame = ctk.CTkLabel(self.main_area, text="📍 Configuración del Parque Eólico", font=ctk.CTkFont(size=18))
        self.current_frame.pack(pady=20)

    def show_simulacion(self):
        self.clear_main_area()
        self.current_frame = ctk.CTkLabel(self.main_area, text="⚡ Parámetros de Simulación", font=ctk.CTkFont(size=18))
        self.current_frame.pack(pady=20)

    def show_resultados(self):
        self.clear_main_area()
        self.current_frame = ctk.CTkLabel(self.main_area, text="📊 Resultados de la Simulación", font=ctk.CTkFont(size=18))
        self.current_frame.pack(pady=20)

    def show_config(self):
        self.clear_main_area()
        self.current_frame = ctk.CTkLabel(self.main_area, text="⚙️ Configuración del Sistema", font=ctk.CTkFont(size=18))
        self.current_frame.pack(pady=20)


if __name__ == "__main__":
    app = EolisimApp()
    app.mainloop()
