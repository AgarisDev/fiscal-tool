# ui.py

import customtkinter as ctk
from PIL import Image, ImageTk
from logic import calcular_ingreso_futuro_desde_inputs, cargar_csv_y_generar_pdf

def iniciar_interfaz():
    ctk.set_appearance_mode("dark")
    ctk.set_default_color_theme("blue")

    ventana = ctk.CTk()
    ventana.geometry("1000x500")
    ventana.title("Herramienta de proyección fiscal")

    frame_izq = ctk.CTkFrame(ventana)
    frame_izq.pack(side="left", fill="both", expand=True, padx=20, pady=20)

    label_titulo = ctk.CTkLabel(frame_izq, text="Calculadora de Ingreso Futuro", font=("Arial", 20, "bold"))
    label_titulo.pack(pady=10)

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
        else:
            resultado_label.configure(text=f"PDF generado: {resultado}")

    boton_calcular = ctk.CTkButton(frame_izq, text="Calcular Ingreso Futuro", command=calcular_desde_inputs)
    boton_calcular.pack(pady=15)

    boton_csv = ctk.CTkButton(frame_izq, text="Cargar CSV y generar PDF", command=cargar_csv)
    boton_csv.pack(pady=5)

    frame_der = ctk.CTkFrame(ventana)
    frame_der.pack(side="right", fill="both", expand=True, padx=20, pady=20)

    img = Image.open("assets/logo.png")
    img = img.resize((400, 150))
    photo = ImageTk.PhotoImage(img)

    label_img = ctk.CTkLabel(frame_der, image=photo, text="")
    label_img.image = photo  # Evita que la imagen se destruya
    label_img.place(relx=0.5, rely=0.5, anchor="center")
    label_img.pack(pady=150, anchor = "center")

    ventana.mainloop()
