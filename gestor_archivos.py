"""
Módulo de lectura/escritura de archivos para el sistema AutoPark.
Centraliza todo el acceso a disco: JSON de entrada y CSV de salida.
"""

import csv
import json
import os


# Nombres de archivos (constantes para evitar typos en todo el código)
ARCHIVO_TARIFAS = "tarifas.json"
ARCHIVO_MOVIMIENTOS = "movimientos.json"
ARCHIVO_LIQUIDACION = "liquidacion.csv"
ARCHIVO_RECHAZADOS = "rechazados.csv"
ARCHIVO_LIQUIDACION_MANUAL = "liquidacion-manual.csv"
ARCHIVO_LIQUIDACION_RANKING = "liquidacion_ranking.csv"



def leer_json(nombre_archivo):
    """
    Lee un archivo JSON y devuelve su contenido como estructura de Python
    (dict o list). Lanza FileNotFoundError si no existe y JSONDecodeError
    si el formato está mal.
    """
    with open(nombre_archivo, "r", encoding="utf-8") as archivo:
        return json.load(archivo)


def cargar_tarifas():
    """Atajo: lee tarifas.json."""
    return leer_json(ARCHIVO_TARIFAS)


def cargar_movimientos():
    """Atajo: lee movimientos.json."""
    return leer_json(ARCHIVO_MOVIMIENTOS)


def escribir_csv(nombre_archivo, filas, columnas, modo="w"):
    """
    Escribe una lista de diccionarios en un CSV.

    Parámetros:
      - nombre_archivo: ruta del CSV de salida.
      - filas: lista de dicts, cada dict es una fila.
      - columnas: lista con los nombres de columnas (orden del encabezado).
      - modo: "w" sobrescribe, "a" agrega al final (append).
    """
    # Si es modo "a" y el archivo no existe, primero escribimos encabezado
    escribir_encabezado = (modo == "w") or (not os.path.exists(nombre_archivo))

    with open(nombre_archivo, modo, newline="", encoding="utf-8") as archivo:
        writer = csv.DictWriter(archivo, fieldnames=columnas)
        if escribir_encabezado:
            writer.writeheader()
        for fila in filas:
            writer.writerow(fila)


def guardar_liquidacion(filas):
    """Escribe liquidacion.csv (sobrescribe)."""
    columnas = [
        "id", "patente", "tipo_vehiculo",
        "entrada", "salida", "minutos", "solicito_lavado",
        "costo_bruto", "bonificacion", "costo_estacionamiento",
        "costo_lavado", "total",
    ]
    escribir_csv(ARCHIVO_LIQUIDACION, filas, columnas, modo="w")


def guardar_rechazados(filas):
    """Escribe rechazados.csv (sobrescribe)."""
    columnas = ["id", "patente", "tipo_vehiculo", "motivo"]
    escribir_csv(ARCHIVO_RECHAZADOS, filas, columnas, modo="w")


def guardar_liquidacion_manual(fila):
    """Agrega una fila al CSV de cobro manual (modo append)."""
    columnas = [
        "patente", "tipo_vehiculo", "dias",
        "entrada", "salida", "minutos", "solicito_lavado",
        "costo_bruto", "bonificacion", "costo_estacionamiento",
        "costo_lavado", "total",
    ]
    escribir_csv(ARCHIVO_LIQUIDACION_MANUAL, [fila], columnas, modo="a")
    
    
def guardar_liquidacion_ranking(filas):
    """Escribe liquidacion_ranking.csv (mismo formato que liquidacion.csv)."""
    columnas = [
        "id", "patente", "tipo_vehiculo",
        "entrada", "salida", "minutos", "solicito_lavado",
        "costo_bruto", "bonificacion", "costo_estacionamiento",
        "costo_lavado", "total",
    ]
    escribir_csv(ARCHIVO_LIQUIDACION_RANKING, filas, columnas, modo="w")    


# ============================================================
# BLOQUE DE PRUEBAS
# ============================================================
if __name__ == "__main__":
    print("=== PRUEBA DE LECTURA DE JSON ===")
    tarifas = cargar_tarifas()
    print(f"  Tipos configurados: {list(tarifas['tarifas'].keys())}")
    print(f"  Tope diario auto:   ${tarifas['tarifas']['auto']['tope_dia']}")

    movimientos = cargar_movimientos()
    print(f"  Movimientos leídos: {len(movimientos['movimientos'])}")
    print(f"  Fecha operación:    {movimientos['fecha_operacion']}")
    print(f"  Primer ID:          {movimientos['movimientos'][0]['id']}")

    print("\n=== PRUEBA DE ESCRITURA DE CSV ===")
    filas_prueba = [
        {"id": "MOV001", "patente": "ABC123", "tipo_vehiculo": "auto",
         "entrada": "08:00", "salida": "08:25", "minutos": 25,
         "solicito_lavado": False, "costo_bruto": 700, "bonificacion": 0,
         "costo_estacionamiento": 700, "costo_lavado": 0, "total": 700},
        {"id": "MOV002", "patente": "AA123BB", "tipo_vehiculo": "moto",
         "entrada": "09:00", "salida": "10:30", "minutos": 90,
         "solicito_lavado": True, "costo_bruto": 1400, "bonificacion": 1400,
         "costo_estacionamiento": 0, "costo_lavado": 2500, "total": 2500},
    ]
    guardar_liquidacion(filas_prueba)
    print("  liquidacion.csv generado con 2 filas.")

    rechazados_prueba = [
        {"id": "MOV031", "patente": "BH123JJ", "tipo_vehiculo": "auto",
         "motivo": "Hora de salida anterior a la entrada"},
    ]
    guardar_rechazados(rechazados_prueba)
    print("  rechazados.csv generado con 1 fila.")

    print("\n  Abrí los CSV con VSCode o Excel para verlos.")