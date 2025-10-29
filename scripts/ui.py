import customtkinter as ctk
from PIL import Image, ImageTk
from logic import calcular_ingreso_futuro_desde_inputs, cargar_csv_y_generar_pdf
from forecast_logic import forecast_proporcional
import json
import os
import tkinter as tk
from tkinter import ttk
from tkinter.filedialog import asksaveasfilename, askdirectory
from tkinter import filedialog
from ttkwidgets.autocomplete import AutocompleteCombobox
import platform

bg = "#1F1F1F"
fg = "#FFFFFF"

is_dark = True

class SearchableDropdown(ctk.CTkFrame):
    def __init__(self, master, values, *args, **kwargs):
        super().__init__(master, *args, **kwargs)
        self.values = values
        self.filtered_values = values
        self.selected_value = None

        style = ttk.Style()
        style.theme_use('alt')
        style.configure('my.TCombobox', arrowsize=20)
        style.configure("TCombobox", fieldbackground="#0092E5")
        style.configure('my.TCombobox.Vertical.TScrollbar', arrowisize=9)

        self.combobox = ttk.Combobox(self, values=self.values, style='my.TCombobox', foreground=bg)

        self.combobox.option_add('*TCombobox*Listbox*Background', bg)
        self.combobox.option_add('*TCombobox*Listbox*Foreground', fg)
        self.combobox.option_add('*TCombobox*Listbox*selectBackground', fg)
        self.combobox.option_add('*TCombobox*Listbox*selectForeground', bg)
        style.map('TCombobox', fieldbackground=[('readonly', bg)])
        style.map('TCombobox', selectedbackground=[('readonly', bg)])
        style.map('TCombobox', selectedforeground=[('readonly', fg)])
        style.map('TCombobox', background=[('readonly', bg)])
        style.map('TCombobox', foreground=[('readonly', bg)])
        self.tk.eval('set popdown [ttk::combobox::PopdownWindow %s]' % self.combobox)
        self.tk.eval(f'$popdown.f.sb configure -style my.TCombobox.Vertical.TScrollbar')

        ttk.Scrollbar(self, orient='vertical')

        self.combobox.pack(side="left", fill="x", expand=True, pady=3)

        self.combobox.bind("<<ComboboxSelected>>", self.on_select)
        self.listbox_update(self.values)

    def listbox_update(self, values):
        self.combobox.configure(values=values)
        if not values:
            self.combobox.set("Cargue CSV para continuar")
        else:
            self.combobox.set("Buscar empresa...")

    def on_keyrelease(self, event):
        typed = self.entry.get().lower()
        self.filtered_values = [v for v in self.values if typed in v.lower()]
        self.listbox_update(self.filtered_values)

    def on_select(self, event):
        self.selected_value = self.combobox.get()

    def get(self):
        valueCb = self.combobox.get()
        if self.selected_value != None:
            return self.selected_value
        elif valueCb != None:
            if (valueCb == "Buscar empresa...") or (valueCb == ""):
                return None
            else:
                return valueCb
        else:
            return None
        
    def enable(self):
        self.combobox.configure(state="normal")

    def disable(self):
        self.combobox.configure(state="disabled")

def iniciar_interfaz(debug: bool = False):
    ctk.set_appearance_mode("dark")
    ctk.set_default_color_theme("blue")

    ventana = ctk.CTk()
    ventana.geometry("950x550")
    ventana.title("Herramienta de proyección fiscal")
    if platform.system() == "Windows":
        ventana.iconphoto(True,tk.PhotoImage(file="assets/fungusIcon.ico"))
    elif platform.system() == "Linux":
        icono=tk.PhotoImage(master=ventana,file="assets/Fungus.png")
        ventana.wm_iconphoto(True,icono)
    else:
        ventana.iconphoto(True,tk.PhotoImage(file="assets/Fungus.png"))

    def clean_label():
        ventana.after(10000, lambda: resultado_label.configure(text=''))

    dark = ImageTk.PhotoImage(file = "assets/dark.png")
    light = ImageTk.PhotoImage(file = "assets/light.png")

    def switch_theme():
        global is_dark

        if is_dark:
            switch_theme_btn.configure(image = dark)
            ctk.set_appearance_mode("light")
            empresa_label.configure(fg_color="#EBEBEB")
            frame_izq.configure(fg_color="transparent")
            canvas.config(bg="#EBEBEB")
            canvas2.config(bg="#EBEBEB")
            canvas3.config(bg="#EBEBEB")
            is_dark = False
        else:
            switch_theme_btn.configure(image = light)
            ctk.set_appearance_mode("dark")
            empresa_label.configure(fg_color="#242424")
            frame_izq.configure(fg_color="transparent")
            canvas.configure(bg="#242424")
            canvas2.configure(bg="#242424")
            canvas3.configure(bg="#242424")
            is_dark = True

    switch_theme_btn = ctk.CTkButton(ventana, image=light, text="", command=switch_theme, height=25, width=25, anchor='nw')
    switch_theme_btn.pack(pady=10, padx=10)


    # === FRAME IZQUIERDO (Formulario) ===
    frame_izq = ctk.CTkFrame(ventana)
    frame_izq.pack(side="left", fill="both", expand=True, padx=20, pady=20)
    frame_izq.configure(fg_color="transparent")

    label_titulo = ctk.CTkLabel(frame_izq, text="Herramienta de Proyección Fiscal", font=("Times New Roman", 20))
    label_titulo.pack(pady=40)

    frame_circle1 = ctk.CTkFrame(frame_izq, fg_color="transparent")
    frame_circle1.pack(pady=10, fill="x")

    frame_textcircle2 = ctk.CTkFrame(frame_izq, fg_color="transparent")
    frame_textcircle2.pack(pady=5, fill="x")

    frame_circle2 = ctk.CTkFrame(frame_izq, fg_color="transparent")
    frame_circle2.pack(pady=1, fill="x")

    frame_circle3 = ctk.CTkFrame(frame_izq, fg_color="transparent")
    frame_circle3.pack(pady=25, fill="x")

    canvas = tk.Canvas(frame_circle1, bg="#242424", height = 40, width = 40, highlightthickness=0)
    canvas.pack(side="left")
    canvas.create_oval(0, 0, 35, 35, fill='#0092E5')
    canvas.create_text(17, 17, text='1', fill='white', font=('Arial', 10))

    boton_calcular = ctk.CTkButton(frame_circle1, anchor='w',text="1.Cargar CSV y generar PDF", fg_color="#0092E5",command=lambda: cargar_csv())
    boton_calcular.pack(pady=10, fill="x")

    resultado_label = ctk.CTkLabel(frame_izq, text="",justify="left", font=("Arial", 14), wraplength=350)
    resultado_label.pack(pady=5)

    empresa_label = ctk.CTkLabel(frame_textcircle2,  anchor='sw', text="             2. Seleccionar empresa", justify="left", font=("Arial", 12), fg_color="#242424")
    empresa_label.pack(pady=5, side=tk.LEFT)

    canvas2 = tk.Canvas(frame_circle2, bg="#242424", height=40, width=40, highlightthickness=0)
    canvas2.pack(side="left")
    canvas2.create_oval(0, 0, 35, 35, fill='#0092E5')
    canvas2.create_text(17, 17, text='2', fill='white', font=('Arial', 10))

    searchable_dropdown = SearchableDropdown(frame_circle2, [])
    searchable_dropdown.pack(pady=1, fill="x", expand=True)
    searchable_dropdown.disable()

    canvas3 = tk.Canvas(frame_circle3, bg='#242424', height=40, width=40, highlightthickness=0)
    canvas3.pack(side="left")
    canvas3.create_oval(0, 0, 35, 35, fill="#0092E5")
    canvas3.create_text(17, 17, text='3', fill='white', font=('Arial', 10))

    boton_forecast = ctk.CTkButton(frame_circle3, anchor='w', text="3. Generar proyección mensual con histórico", fg_color="#0092E5", command=lambda: generar_forecast())
    boton_forecast.pack(pady=25, fill="x")

    clean_label()

    def cargar_csv():
        resultado, error = cargar_csv_y_generar_pdf()
        if error:
            resultado_label.configure(text=error)
            searchable_dropdown.values = []
            searchable_dropdown.listbox_update([])
            searchable_dropdown.disable()
        else:
            resultado_label.configure(text=f"PDF generado: {resultado}")
            json_path = "resultados.json"
            if os.path.exists(json_path):
                with open(json_path, "r", encoding="utf-8") as f:
                    data = json.load(f)
                company_names = [item.get("NOMBRE", "") for item in data if "NOMBRE" in item]
                if company_names:
                    searchable_dropdown.values = company_names
                    searchable_dropdown.listbox_update(company_names)
                    searchable_dropdown.enable()
        clean_label()

    def generar_forecast():
        empresa = searchable_dropdown.get()

        if empresa is None:
            resultado_label.configure(text="No has seleccionado alguna empresa, selecciona una")
            return

        with open("resultados.json", "r", encoding="utf-8") as f:
            data = json.load(f)
        resultado_empresa = next((item for item in data if item.get("NOMBRE") == empresa), None)
        if not resultado_empresa:
            resultado_label.configure(text="Empresa no encontrada en JSON.")
            return
        
        ingreso_futuro = resultado_empresa.get("IF")
        deducciones_futuras = resultado_empresa.get("DF")
        mes_actual = resultado_empresa.get("MES")

        if not all(isinstance(val, (int, float)) for val in [ingreso_futuro, deducciones_futuras]) or not isinstance(mes_actual, int):
            resultado_label.configure(text="Datos inválidos en JSON para esta empresa.")
            return

        file_path = filedialog.askopenfilename(title="Cargar histórico" ,filetypes=[("CSV Files", "*.csv")])
        if not file_path:
            resultado_label.configure(text="Carga del csv cancelada por el usuario")
            return
        
        ruta_salida = askdirectory(
            title="Guardar proyección mensual en..."
        )

        if not ruta_salida:
            resultado_label.configure(text="Guardado cancelado por el usuario")
            return

        try:
            ruta_salida, tabla = forecast_proporcional(
                json_path="resultados.json",
                hist_csv_path=file_path,
                html_output=ruta_salida,
                nombre_empresa=empresa,
            )
            resultado_label.configure(text=f"Proyección generada en:\n{ruta_salida}")
        except Exception as e:
            resultado_label.configure(text=f"Error al generar proyección: {e}")

    # === FRAME DERECHO (Imagen) ===
    frame_der = ctk.CTkFrame(ventana)
    frame_der.pack(side="right", fill="both", expand=True, padx=30, pady=30)

    if is_dark:
        img = Image.open("assets/logo.png")
        img = img.resize((280, 90))
        photo = ImageTk.PhotoImage(img)
    else:
        img = Image.open("assets/logo2.png")
        img = img.resize((280, 90))
        photo = ImageTk.PhotoImage(img)

    label_img = ctk.CTkLabel(frame_der, image=photo, text="")
    label_img.image = photo
    label_img.place(relx=0.5, rely=0.5, anchor=tk.CENTER)

    ventana.mainloop()