"""
Módulo de cálculos contables del sistema AutoPark.
Contiene la función recursiva obligatoria y la liquidación completa.
"""

import json


def calcular_estacionamiento_recursivo(minutos_restantes, tipo_vehiculo, tarifas):
    """
    Calcula el costo BRUTO de estacionamiento por tramos (RECURSIVO).
    NO aplica tope diario ni bonificaciones. Solo el cálculo base.
    """
    if minutos_restantes <= 0:
        return 0

    tarifa = tarifas["tarifas"][tipo_vehiculo]

    if minutos_restantes > 120:
        return tarifa["precio_hora_adicional"] + calcular_estacionamiento_recursivo(
            minutos_restantes - 60, tipo_vehiculo, tarifas
        )

    return tarifa["precio_bloque_30min"] + calcular_estacionamiento_recursivo(
        minutos_restantes - 30, tipo_vehiculo, tarifas
    )


def calcular_liquidacion(minutos, tipo_vehiculo, dias, solicito_lavado, tarifas):
    """
    Calcula la liquidación COMPLETA y devuelve un diccionario con el desglose.

    Reglas aplicadas (en orden):
      1. Si dias > 0 -> costo fijo por día (dias * tope_dia). No usa minutos.
      2. Si dias == 0:
         - Costo bruto = recursivo(minutos) recortado al tope_dia.
         - Sin lavado: paga el costo con tope.
         - Con lavado y minutos <= 120: estacionamiento 100% bonificado.
         - Con lavado y minutos > 120: paga SOLO el excedente (bloques de 60).
      3. Lavado (si aplica) se suma siempre al final.
    """
    tarifa = tarifas["tarifas"][tipo_vehiculo]
    tope = tarifa["tope_dia"]
    precio_lavado = tarifa["precio_lavado"]

    resultado = {
        "minutos": minutos,
        "dias": dias,
        "tipo_vehiculo": tipo_vehiculo,
        "solicito_lavado": solicito_lavado,
        "costo_bruto": 0,          # costo teórico antes de bonificar
        "bonificacion": 0,          # ahorro por lavado
        "costo_estacionamiento": 0, # lo que efectivamente paga de estacionamiento
        "costo_lavado": 0,
        "total": 0,
    }

    # ---------- CASO 1: ESTADÍA PROLONGADA (días > 0) ----------
    if dias > 0:
        costo = dias * tope
        resultado["costo_bruto"] = costo
        resultado["costo_estacionamiento"] = costo
        resultado["costo_lavado"] = precio_lavado if solicito_lavado else 0
        resultado["total"] = resultado["costo_estacionamiento"] + resultado["costo_lavado"]
        return resultado

    # ---------- CASO 2: MISMO DÍA (días = 0) ----------
    costo_recursivo = calcular_estacionamiento_recursivo(minutos, tipo_vehiculo, tarifas)
    costo_con_tope = min(costo_recursivo, tope)
    resultado["costo_bruto"] = costo_con_tope

    if not solicito_lavado:
        # Sin lavado: paga el costo con tope aplicado
        resultado["costo_estacionamiento"] = costo_con_tope

    elif minutos <= 120:
        # Con lavado, hasta 2 hs: estacionamiento 100% bonificado
        resultado["bonificacion"] = costo_con_tope
        resultado["costo_estacionamiento"] = 0

    else:
        # Con lavado, más de 2 hs: paga SOLO el excedente en bloques de 60
        excedente = minutos - 120
        bloques_hora = (excedente + 59) // 60   # redondeo ↑ sin math.ceil
        costo_excedente = bloques_hora * tarifa["precio_hora_adicional"]
        costo_excedente = min(costo_excedente, tope)  # el tope también aplica acá
        resultado["bonificacion"] = costo_con_tope - costo_excedente
        resultado["costo_estacionamiento"] = costo_excedente

    # Sumamos el lavado si corresponde
    resultado["costo_lavado"] = precio_lavado if solicito_lavado else 0
    resultado["total"] = resultado["costo_estacionamiento"] + resultado["costo_lavado"]
    return resultado


# ============================================================
# BLOQUE DE PRUEBAS
# ============================================================
if __name__ == "__main__":
    with open("tarifas.json", "r", encoding="utf-8") as archivo:
        tarifas = json.load(archivo)

    print("=== PRUEBAS DE LA FUNCIÓN RECURSIVA (sin tope) ===")
    pruebas = [0, 15, 30, 45, 60, 90, 120, 121, 150, 180, 210, 240]
    for minutos in pruebas:
        costo = calcular_estacionamiento_recursivo(minutos, "auto", tarifas)
        print(f"  {minutos:>3} min -> ${costo}")

    print()
    print("=== PRUEBAS DE LIQUIDACIÓN COMPLETA ===")

    casos = [
        # (descripción, minutos, tipo, dias, lavado)
        ("Auto 15 min sin lavado",             15,   "auto",      0, False),
        ("Auto 90 min sin lavado",             90,   "auto",      0, False),
        ("Auto 210 min sin lavado",            210,  "auto",      0, False),
        ("Auto 900 min sin lavado (TOPE)",     900,  "auto",      0, False),
        ("Auto 60 min CON lavado",             60,   "auto",      0, True),
        ("Auto 210 min CON lavado",            210,  "auto",      0, True),
        ("Auto 1440 min CON lavado (TOPE)",    1440, "auto",      0, True),
        ("Moto 3 días sin lavado",             0,    "moto",      3, False),
        ("Camioneta 2 días CON lavado",        0,    "camioneta", 2, True),
    ]

    for desc, minutos, tipo, dias, lavado in casos:
        r = calcular_liquidacion(minutos, tipo, dias, lavado, tarifas)
        print(f"\n  {desc}:")
        print(f"    Costo bruto            : ${r['costo_bruto']}")
        print(f"    Bonificación por lavado: -${r['bonificacion']}")
        print(f"    Costo estacionamiento  : ${r['costo_estacionamiento']}")
        print(f"    Costo lavado           : ${r['costo_lavado']}")
        print(f"    TOTAL A PAGAR          : ${r['total']}")