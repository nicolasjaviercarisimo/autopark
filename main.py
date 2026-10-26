"""
Menú principal del sistema AutoPark.
Punto de entrada de la aplicación.
"""

import calculos
import validaciones
import gestor_archivos


# ============================================================
# OPCIÓN 2: PROCESAMIENTO POR LOTE
# ============================================================
def procesar_lote():
    """
    Lee movimientos.json, valida cada registro y genera
    liquidacion.csv (válidos) + rechazados.csv (inválidos).
    """
    print("\n--- PROCESAMIENTO POR LOTE ---")

    # 1. Leer los archivos de entrada
    try:
        tarifas = gestor_archivos.cargar_tarifas()
        datos = gestor_archivos.cargar_movimientos()
    except FileNotFoundError as e:
        print(f"  ❌ Error: no se encontró el archivo '{e.filename}'")
        return
    except Exception as e:
        print(f"  ❌ Error al leer archivos: {e}")
        return

    movimientos = datos["movimientos"]
    print(f"  Total movimientos a procesar: {len(movimientos)}")

    liquidaciones = []
    rechazados = []

    # 2. Procesar cada movimiento
    for mov in movimientos:
        id_mov = mov.get("id", "?")

        # --- 2.a Validar patente ---
        patente_norm = validaciones.normalizar_patente(mov.get("patente", ""))
        if not validaciones.validar_patente(patente_norm):
            rechazados.append({
                "id": id_mov,
                "patente": mov.get("patente", ""),
                "tipo_vehiculo": mov.get("tipo_vehiculo", ""),
                "motivo": f"Patente inválida: {mov.get('patente', '')!r}",
            })
            continue

        # --- 2.b Validar tipo ---
        tipo_norm = validaciones.normalizar_tipo(mov.get("tipo_vehiculo", ""))
        if not validaciones.validar_tipo(tipo_norm):
            rechazados.append({
                "id": id_mov,
                "patente": patente_norm,
                "tipo_vehiculo": mov.get("tipo_vehiculo", ""),
                "motivo": f"Tipo de vehículo inválido: {mov.get('tipo_vehiculo', '')!r}",
            })
            continue

        # --- 2.c Validar horas ---
        entrada_norm = validaciones.normalizar_hora(mov.get("entrada", ""))
        salida_norm = validaciones.normalizar_hora(mov.get("salida", ""))

        if not validaciones.validar_hora(entrada_norm):
            rechazados.append({
                "id": id_mov,
                "patente": patente_norm,
                "tipo_vehiculo": tipo_norm,
                "motivo": f"Hora de entrada inválida: {mov.get('entrada', '')!r}",
            })
            continue

        if not validaciones.validar_hora(salida_norm):
            rechazados.append({
                "id": id_mov,
                "patente": patente_norm,
                "tipo_vehiculo": tipo_norm,
                "motivo": f"Hora de salida inválida: {mov.get('salida', '')!r}",
            })
            continue

        # --- 2.d Calcular minutos y validar salida > entrada ---
        minutos_entrada = validaciones.hora_a_minutos(entrada_norm)
        minutos_salida = validaciones.hora_a_minutos(salida_norm)

        if minutos_salida <= minutos_entrada:
            rechazados.append({
                "id": id_mov,
                "patente": patente_norm,
                "tipo_vehiculo": tipo_norm,
                "motivo": (
                    f"Hora de salida ({salida_norm}) anterior o igual "
                    f"a la de entrada ({entrada_norm})"
                ),
            })
            continue

        minutos = minutos_salida - minutos_entrada
        lavado = bool(mov.get("solicito_lavado", False))

        # --- 2.e Calcular liquidación ---
        resultado = calculos.calcular_liquidacion(
            minutos, tipo_norm, dias=0, solicito_lavado=lavado, tarifas=tarifas
        )

        liquidaciones.append({
            "id": id_mov,
            "patente": patente_norm,
            "tipo_vehiculo": tipo_norm,
            "entrada": entrada_norm,
            "salida": salida_norm,
            "minutos": minutos,
            "solicito_lavado": lavado,
            "costo_bruto": resultado["costo_bruto"],
            "bonificacion": resultado["bonificacion"],
            "costo_estacionamiento": resultado["costo_estacionamiento"],
            "costo_lavado": resultado["costo_lavado"],
            "total": resultado["total"],
        })

    # 3. Escribir CSVs
    gestor_archivos.guardar_liquidacion(liquidaciones)
    gestor_archivos.guardar_rechazados(rechazados)

    # 3.b Generar ranking ordenado por total (mayor a menor) — Desafío #3
    ranking = sorted(liquidaciones, key=lambda x: x["total"], reverse=True)
    gestor_archivos.guardar_liquidacion_ranking(ranking)

    # 4. Resumen en consola
    total_recaudado = sum(l["total"] for l in liquidaciones)
    print(f"\n  ✅ Procesados: {len(liquidaciones)}")
    print(f"  ❌ Rechazados: {len(rechazados)}")
    print(f"  💰 Total recaudado: ${total_recaudado}")
    print("\n  Archivos generados: liquidacion.csv, rechazados.csv, liquidacion_ranking.csv")
    print(f"  🏆 Top 3 mayores cobros:")
    for i, fila in enumerate(ranking[:3], start=1):
        print(f"     {i}. {fila['patente']} ({fila['tipo_vehiculo']}) -> ${fila['total']}")

    # 5. Reporte estadístico (Desafío #2)
    generar_reporte_estadistico(liquidaciones)


# ============================================================
# DESAFÍO #2: REPORTE ESTADÍSTICO DEL LOTE
# ============================================================
def generar_reporte_estadistico(liquidaciones):
    """
    Imprime un reporte ejecutivo con métricas avanzadas del lote procesado:
      - Categoría más rentable (mayor recaudación en $).
      - Porcentaje de vehículos que contrataron lavado.
      - Estadía promedio (en minutos) por categoría.
    """
    if not liquidaciones:
        print("\n  ⚠️  No hay datos para generar el reporte estadístico.")
        return

    total_vehiculos = len(liquidaciones)

    # --- Acumuladores por tipo ---
    recaudacion_por_tipo = {}
    cantidad_por_tipo = {}
    minutos_por_tipo = {}

    # --- Contadores globales ---
    con_lavado = 0

    for fila in liquidaciones:
        tipo = fila["tipo_vehiculo"]

        # Acumulamos por tipo
        recaudacion_por_tipo[tipo] = recaudacion_por_tipo.get(tipo, 0) + fila["total"]
        cantidad_por_tipo[tipo] = cantidad_por_tipo.get(tipo, 0) + 1
        minutos_por_tipo[tipo] = minutos_por_tipo.get(tipo, 0) + fila["minutos"]

        # Contamos los que pidieron lavado
        if fila["solicito_lavado"]:
            con_lavado += 1

    # --- Métrica 1: categoría más rentable ---
    tipo_mas_rentable = max(recaudacion_por_tipo, key=recaudacion_por_tipo.get)
    monto_maximo = recaudacion_por_tipo[tipo_mas_rentable]

    # --- Métrica 2: porcentaje con lavado ---
    porcentaje_lavado = (con_lavado / total_vehiculos) * 100

    # --- Mostrar reporte ---
    print()
    print("=" * 50)
    print("   📊 REPORTE ESTADÍSTICO DEL NEGOCIO")
    print("=" * 50)
    print(f"  Total de vehículos procesados: {total_vehiculos}")
    print()
    print(f"  🏆 Categoría más rentable: {tipo_mas_rentable} (${monto_maximo})")
    print()
    print(f"  🧼 Vehículos con lavado: {con_lavado} de {total_vehiculos} "
          f"({porcentaje_lavado:.1f}%)")
    print()
    print("  ⏱️  Estadía promedio por categoría:")
    for tipo in cantidad_por_tipo:
        promedio = minutos_por_tipo[tipo] / cantidad_por_tipo[tipo]
        print(f"     - {tipo:>10}: {promedio:6.1f} min "
              f"(sobre {cantidad_por_tipo[tipo]} vehículos)")
    print("=" * 50)


# ============================================================
# OPCIÓN 1: COBRO MANUAL EN VENTANILLA
# ============================================================
def pedir_patente():
    """Pide patente hasta que sea válida (normaliza y valida)."""
    while True:
        patente = input("  Patente (ej. ABC123 o AA123BB): ").strip()
        norm = validaciones.normalizar_patente(patente)
        if validaciones.validar_patente(norm):
            return norm
        print("  ❌ Patente inválida. Formatos: ABC123 (3 letras + 3 números) "
              "o AA123BB (2 letras + 3 números + 2 letras).")


def pedir_tipo():
    """Pide tipo de vehículo hasta que sea válido."""
    while True:
        tipo = input("  Tipo de vehículo (auto/moto/camioneta): ").strip()
        norm = validaciones.normalizar_tipo(tipo)
        if validaciones.validar_tipo(norm):
            return norm
        print("  ❌ Tipo inválido. Debe ser: auto, moto o camioneta.")


def pedir_dias():
    """Pide cantidad de días (entero >= 0)."""
    while True:
        entrada = input("  ¿Cuántos días pasaron? (0 si se retira en el mismo día): ").strip()
        try:
            dias = int(entrada)
            if dias < 0:
                print("  ❌ Los días no pueden ser negativos.")
                continue
            return dias
        except ValueError:
            print("  ❌ Ingresá un número entero (0, 1, 2, ...).")


def pedir_hora(mensaje):
    """Pide una hora HH:MM hasta que sea válida."""
    while True:
        hora = input(f"  {mensaje}: ").strip()
        norm = validaciones.normalizar_hora(hora)
        if validaciones.validar_hora(norm):
            return norm
        print("  ❌ Hora inválida. Formato HH:MM (ej. 08:30, 17:45).")


def pedir_lavado():
    """Pide S/N y devuelve True/False."""
    while True:
        resp = input("  ¿Solicitó lavado? (S/N): ").strip().upper()
        if resp in ("S", "N"):
            return resp == "S"
        print("  ❌ Respondé S o N.")


def cobro_manual():
    """Flujo completo de cobro manual en ventanilla."""
    print("\n--- COBRO MANUAL EN VENTANILLA ---")

    # 1. Cargar tarifas
    try:
        tarifas = gestor_archivos.cargar_tarifas()
    except FileNotFoundError as e:
        print(f"  ❌ Error: no se encontró el archivo '{e.filename}'")
        return
    except Exception as e:
        print(f"  ❌ Error al leer tarifas: {e}")
        return

    # 2. Pedir y validar datos
    patente = pedir_patente()
    tipo = pedir_tipo()
    dias = pedir_dias()

    if dias == 0:
        # Estadía del mismo día: pedir entrada y salida
        entrada = pedir_hora("Hora de entrada (HH:MM)")
        salida = pedir_hora("Hora de salida (HH:MM)")

        min_entrada = validaciones.hora_a_minutos(entrada)
        min_salida = validaciones.hora_a_minutos(salida)

        if min_salida <= min_entrada:
            print(f"\n  ❌ La salida ({salida}) debe ser posterior a la entrada ({entrada}).")
            print("  Operación cancelada. Volvé a intentar desde el menú.")
            return

        minutos = min_salida - min_entrada
    else:
        # Estadía prolongada: solo entrada, no se pide salida
        entrada = pedir_hora("Hora de entrada (HH:MM)")
        salida = ""
        minutos = 0
        print(f"  ℹ️  Estadía prolongada: se liquidarán {dias} día(s) completo(s).")

    lavado = pedir_lavado()

    # 3. Calcular liquidación
    resultado = calculos.calcular_liquidacion(minutos, tipo, dias, lavado, tarifas)

    # 4. Mostrar desglose en pantalla
    print("\n  ---------- DESGLOSE CONTABLE ----------")
    print(f"  Patente:                {patente}")
    print(f"  Tipo:                   {tipo}")
    print(f"  Días:                   {dias}")
    print(f"  Hora de entrada:        {entrada}")
    print(f"  Hora de salida:         {salida if salida else '(no aplica)'}")
    print(f"  Minutos estacionado:    {minutos}")
    print(f"  ¿Solicitó lavado?:      {'Sí' if lavado else 'No'}")
    print(f"  Costo bruto:            ${resultado['costo_bruto']}")
    print(f"  Bonificación por lavado:-${resultado['bonificacion']}")
    print(f"  Costo estacionamiento:  ${resultado['costo_estacionamiento']}")
    print(f"  Costo lavado:           ${resultado['costo_lavado']}")
    print("  ---------------------------------------")
    print(f"  TOTAL A PAGAR:          ${resultado['total']}")

    # 5. Guardar en CSV (append)
    fila = {
        "patente": patente,
        "tipo_vehiculo": tipo,
        "dias": dias,
        "entrada": entrada,
        "salida": salida,
        "minutos": minutos,
        "solicito_lavado": lavado,
        "costo_bruto": resultado["costo_bruto"],
        "bonificacion": resultado["bonificacion"],
        "costo_estacionamiento": resultado["costo_estacionamiento"],
        "costo_lavado": resultado["costo_lavado"],
        "total": resultado["total"],
    }
    gestor_archivos.guardar_liquidacion_manual(fila)
    print("\n  ✅ Comprobante guardado en liquidacion-manual.csv")


# ============================================================
# MENÚ PRINCIPAL
# ============================================================
def mostrar_menu():
    while True:
        print()
        print("=" * 50)
        print("   SISTEMA DE GESTIÓN DE ESTACIONAMIENTO AUTOPARK")
        print("=" * 50)
        print("1. Registrar / Consultar cobro manual")
        print("2. Procesar lote de movimientos (JSON -> CSV)")
        print("3. Salir")
        opcion = input("Seleccione una opción: ").strip()

        if opcion == "1":
            cobro_manual()
        elif opcion == "2":
            procesar_lote()
        elif opcion == "3":
            print("\n  ¡Hasta luego!")
            break
        else:
            print("  ❌ Opción inválida. Elegí 1, 2 o 3.")


if __name__ == "__main__":
    mostrar_menu()