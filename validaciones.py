"""
Módulo de validaciones y normalización del sistema AutoPark.
"""

import re


# Patrones de patentes (compilados una sola vez por eficiencia)
PATRON_TRADICIONAL = re.compile(r"^[A-Z]{3}\d{3}$")
PATRON_MERCOSUR = re.compile(r"^[A-Z]{2}\d{3}[A-Z]{2}$")
PATRON_HORA = re.compile(r"^([01]\d|2[0-3]):([0-5]\d)$")

TIPOS_VALIDOS = {"auto", "moto", "camioneta"}


def normalizar_patente(patente):
    """
    Limpia la patente: quita TODOS los espacios (externos e internos) y
    pasa a mayúsculas.
    Ejemplo: '  BF 901 GG ' -> 'BF901GG'
    """
    if not isinstance(patente, str):
        return ""
    return patente.replace(" ", "").upper()


def validar_patente(patente_normalizada):
    """
    Devuelve True si la patente (ya normalizada) cumple con algún formato
    oficial (tradicional o Mercosur). Si no, False.
    """
    return bool(
        PATRON_TRADICIONAL.match(patente_normalizada)
        or PATRON_MERCOSUR.match(patente_normalizada)
    )


def normalizar_tipo(tipo):
    """
    Limpia el tipo de vehículo: quita espacios y pasa a minúsculas.
    Ejemplo: '  MOTO  ' -> 'moto'
    """
    if not isinstance(tipo, str):
        return ""
    return tipo.strip().lower()


def validar_tipo(tipo_normalizado):
    """True si el tipo pertenece a los admitidos."""
    return tipo_normalizado in TIPOS_VALIDOS


def normalizar_hora(hora):
    """
    Acepta 'H:MM' o 'HH:MM' y devuelve siempre 'HH:MM' con ceros a la izquierda.
    Ejemplo: '8:5' -> '08:05'
    """
    if not isinstance(hora, str):
        return ""
    hora = hora.strip()
    partes = hora.split(":")
    if len(partes) != 2:
        return hora  # dejamos que el validador lo rechace
    hh, mm = partes
    if not (hh.isdigit() and mm.isdigit()):
        return hora
    return f"{int(hh):02d}:{int(mm):02d}"


def validar_hora(hora_normalizada):
    """True si la hora tiene formato HH:MM y está entre 00:00 y 23:59."""
    return bool(PATRON_HORA.match(hora_normalizada))


def hora_a_minutos(hora_normalizada):
    """Convierte 'HH:MM' a minutos totales desde las 00:00. '08:30' -> 510."""
    hh, mm = hora_normalizada.split(":")
    return int(hh) * 60 + int(mm)


# ============================================================
# BLOQUE DE PRUEBAS
# ============================================================
if __name__ == "__main__":
    print("=== PRUEBAS DE PATENTES ===")
    pruebas_patentes = [
        "  abc123  ",
        "AA123BB",
        "  BF 901 GG ",
        "123ABC",        # inválida: empieza con números
        "MOTO12",        # inválida: 4 letras + 2 números
        "PATENTE99",     # inválida
        "ABC-123",       # inválida: tiene guión
        "",
    ]
    for p in pruebas_patentes:
        norm = normalizar_patente(p)
        ok = validar_patente(norm)
        estado = "✅ VÁLIDA" if ok else "❌ INVÁLIDA"
        print(f"  {repr(p):<20} -> {repr(norm):<12} {estado}")

    print("\n=== PRUEBAS DE TIPO ===")
    for t in ["  MOTO  ", "Auto", "camioneta", "tractor", "AUTO"]:
        norm = normalizar_tipo(t)
        ok = validar_tipo(norm)
        estado = "✅ VÁLIDO" if ok else "❌ INVÁLIDO"
        print(f"  {repr(t):<15} -> {repr(norm):<12} {estado}")

    print("\n=== PRUEBAS DE HORA ===")
    for h in ["08:00", "8:5", "23:59", "24:00", "12:60", "abc", ""]:
        norm = normalizar_hora(h)
        ok = validar_hora(norm)
        estado = "✅ VÁLIDA" if ok else "❌ INVÁLIDA"
        print(f"  {repr(h):<10} -> {repr(norm):<8} {estado}")