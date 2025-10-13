import os
ruta_base = "SistemaGestionBiblioteca"
archivo_salida = "todo_el_codigo.txt"
with open(archivo_salida, "w", encoding="utf-8") as salida:
    for carpeta_raiz, subcarpetas, archivos in os.walk(ruta_base):
        for nombre_archivo in archivos:
            if nombre_archivo.endswith(".py"):
                ruta_archivo = os.path.join(carpeta_raiz, nombre_archivo)
                salida.write(f"\n\n# ==== {ruta_archivo} ====\n\n")
                with open(ruta_archivo, "r", encoding="utf-8") as f:
                    salida.write(f.read())
print(f"✅ Código unido en el archivo: {archivo_salida}")
