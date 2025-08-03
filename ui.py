import customtkinter as ctk
from PIL import Image, ImageTk
from logic import calcular_ingreso_futuro_desde_inputs, cargar_csv_y_generar_pdf
import json
import os
import tkinter as tk  # Para Listbox y scrollbar

class SearchableDropdown(ctk.CTkFrame):
    def __init__(self, master, values, *args, **kwargs):
        super().__init__(master, *args, **kwargs)
        self.values = values
        self.filtered_values = values

        self.entry = ctk.CTkEntry(self)
        self.entry.pack(fill="x", padx=5, pady=(5,0))
        self.entry.bind("<KeyRelease>", self.on_keyrelease)

        # Frame para listbox + scrollbar
        listbox_frame = ctk.CTkFrame(self)
        listbox_frame.pack(fill="x", padx=5, pady=(0,5), expand=False)

        self.scrollbar = tk.Scrollbar(listbox_frame, orient="vertical")
        self.scrollbar.pack(side="right", fill="y")

        self.listbox = tk.Listbox(
            listbox_frame,
            height=6,
            yscrollcommand=self.scrollbar.set,
            bg="#1F1F1F",       # fondo oscuro
            fg="white",          # texto blanco
            selectbackground="#3A7FF6",
            activestyle="none",
            highlightthickness=0,
            borderwidth=0,
        )
        self.listbox.pack(side="left", fill="both", expand=True)
        self.scrollbar.config(command=self.listbox.yview)

        self.listbox.bind("<<ListboxSelect>>", self.on_select)
        self.listbox_update(self.values)

        self.selected_value = None

    def listbox_update(self, values):
        self.listbox.delete(0, "end")
        for v in values:
            self.listbox.insert("end", v)

    def on_keyrelease(self, event):
        typed = self.entry.get().lower()
        self.filtered_values = [v for v in self.values if typed in v.lower()]
        self.listbox_update(self.filtered_values)

    def on_select(self, event):
        selected_indices = self.listbox.curselection()
        if selected_indices:
            index = selected_indices[0]
            self.selected_value = self.filtered_values[index]
            self.entry.delete(0, "end")
            self.entry.insert(0, self.selected_value)
            self.listbox_update(self.filtered_values)

    def get(self):
        return self.selected_value

    def enable(self):
        self.entry.configure(state="normal")
        self.listbox.configure(state="normal")
        # No tocar scrollbar

    def disable(self):
        self.entry.configure(state="disabled")
        self.listbox.configure(state="disabled")
        # No tocar scrollbar


def iniciar_interfaz(debug: bool = False):
    ctk.set_appearance_mode("dark")
    ctk.set_default_color_theme("blue")

    ventana = ctk.CTk()
    ventana.geometry("1000x650")
    ventana.title("Herramienta de proyección fiscal")

    frame_izq = ctk.CTkFrame(ventana)
    frame_izq.pack(side="left", fill="both", expand=True, padx=20, pady=20)

    label_titulo = ctk.CTkLabel(frame_izq, text="Calculadora de Ingreso Futuro", font=("Arial", 20, "bold"))
    label_titulo.pack(pady=10)
    if debug:
        entry_CUo = ctk.CTkEntry(frame_izq, placeholder_text="Costo Unitario Objetivo (CUo)")
        entry_CUo.pack(pady=5)

        entry_Ua = ctk.CTkEntry(frame_izq, placeholder_text="Utilidad Acumulada (Ua)")
        entry_Ua.pack(pady=5)

        entry_Ia = ctk.CTkEntry(frame_izq, placeholder_text="Ingreso Acumulado (Ia)")
        entry_Ia.pack(pady=5)

        entry_Deducciones = ctk.CTkEntry(frame_izq, placeholder_text="Deducciones Acumuladas")
        entry_Deducciones.pack(pady=5)

        entry_mes_actual = ctk.CTkEntry(frame_izq, placeholder_text="Mes actual (1-12)")
        entry_mes_actual.pack(pady=5)

    resultado_label = ctk.CTkLabel(frame_izq, text="", font=("Arial", 16))
    resultado_label.pack(pady=5)

    searchable_dropdown = SearchableDropdown(frame_izq, [])
    searchable_dropdown.pack(pady=10, fill="x")
    searchable_dropdown.disable()

    boton_calcular = ctk.CTkButton(frame_izq, text="Calcular Ingreso Futuro", command=lambda: calcular_desde_inputs())
    boton_calcular.pack(pady=15, fill="x")

    boton_csv = ctk.CTkButton(frame_izq, text="Cargar CSV y generar PDF", command=lambda: cargar_csv())
    boton_csv.pack(pady=5, fill="x")

    def calcular_desde_inputs():
        try:
            cuo = float(entry_CUo.get())
            ua = float(entry_Ua.get())
            ia = float(entry_Ia.get())
            ded = float(entry_Deducciones.get())
            mes = int(entry_mes_actual.get())

            resultado, error = calcular_ingreso_futuro_desde_inputs(cuo, ua, ia, ded, mes)
            if error:
                resultado_label.configure(text=error)
            else:
                resultado_label.configure(text=f"Ingreso Futuro Necesario: ${resultado:,.2f}")
        except ValueError:
            resultado_label.configure(text="Error: Introduce solo números válidos.")

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
                try:
                    with open(json_path, "r", encoding="utf-8") as f:
                        data = json.load(f)
                    company_names = [item.get("NOMBRE", "") for item in data if "NOMBRE" in item]

                    if company_names:
                        searchable_dropdown.values = company_names
                        searchable_dropdown.listbox_update(company_names)
                        searchable_dropdown.enable()
                    else:
                        searchable_dropdown.values = []
                        searchable_dropdown.listbox_update([])
                        searchable_dropdown.disable()
                        resultado_label.configure(text="No se encontraron empresas en el JSON.")
                except Exception as e:
                    resultado_label.configure(text=f"Error leyendo JSON: {e}")
                    searchable_dropdown.values = []
                    searchable_dropdown.listbox_update([])
                    searchable_dropdown.disable()
            else:
                resultado_label.configure(text="Archivo JSON no encontrado.")
                searchable_dropdown.values = []
                searchable_dropdown.listbox_update([])
                searchable_dropdown.disable()

    frame_der = ctk.CTkFrame(ventana)
    frame_der.pack(side="right", fill="both", expand=True, padx=20, pady=20)

    img = Image.open("assets/logo.png")
    img = img.resize((400, 150))
    photo = ImageTk.PhotoImage(img)

    label_img = ctk.CTkLabel(frame_der, image=photo, text="")
    label_img.image = photo  # Evita que la imagen se destruya
    label_img.place(relx=0.5, rely=0.5, anchor="center")
    label_img.pack(pady=150, anchor="center")

    ventana.mainloop()
