import sys
import os
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from datos.grafo_base import cargar_nodos, haversine
import json

#---Cargar pedidos desde JSON
def cargar_pedidos(ruta_json="datos/pedidos.json"):
    with open(ruta_json, "r", encoding="utf-8") as f:
        data = json.load(f)
    return data["pedidos"]


# ----------------------------------------------------------------
#  UTILIDAD: convertir peso float → entero escalado
#  El Knapsack clásico necesita índices enteros.
#  Multiplicamos por ESCALA para conservar 1 decimal de precisión.
#  Ej: 3.5 kg → 35  |  12.0 kg → 120
# ----------------------------------------------------------------
ESCALA = 10  #---factor de escala para manejar decimales en el peso


def discretizar_peso(peso_kg):
    #---Convierte un peso float a entero escalado para indexar la tabla DP
    #---Ejemplo: 4.5 kg → 45 (índice entero)
    return round(peso_kg * ESCALA)


# ----------------------------------------------------------------
#  KNAPSACK — TABULACIÓN (bottom-up)
#
#  Construye una tabla dp[i][w]:
#    = valor máximo usando los primeros i pedidos
#      con capacidad de peso w (escalada)
#
#  Cada celda se llena UNA SOLA VEZ comparando:
#    - No incluir pedido i → dp[i-1][w]
#    - Incluir pedido i   → dp[i-1][w - peso_i] + valor_i
#  y tomando el máximo de ambas opciones.
#
#  Complejidad: O(n * W) tiempo y espacio
# ----------------------------------------------------------------
def knapsack_tabulacion(pedidos, capacidad_kg):
    #---Total de pedidos disponibles
    n = len(pedidos)

    #---Capacidad máxima en unidades escaladas (entero)
    W = discretizar_peso(capacidad_kg)

    #---Tabla DP de (n+1) filas × (W+1) columnas, iniciada en ceros
    #---dp[i][w] = mejor valor usando los primeros i pedidos con capacidad w
    dp = [[0.0] * (W + 1) for _ in range(n + 1)]

    #---Llenamos la tabla fila por fila (cada fila = un pedido)
    for i in range(1, n + 1):
        pedido = pedidos[i - 1]                    #---pedido actual (índice base 0)
        w_pedido = discretizar_peso(pedido["peso"]) #---peso del pedido escalado
        v_pedido = pedido["valor"]                  #---valor del pedido en soles

        for w in range(W + 1):                     #---recorre cada capacidad posible
            #---Opción 1: no incluir este pedido → heredamos el valor anterior
            dp[i][w] = dp[i - 1][w]

            #---Opción 2: incluir este pedido, solo si cabe en la capacidad w
            if w_pedido <= w:
                valor_con = dp[i - 1][w - w_pedido] + v_pedido
                if valor_con > dp[i][w]:            #---¿conviene incluirlo?
                    dp[i][w] = valor_con

    #---Backtracking: reconstruir qué pedidos fueron seleccionados
    #---Recorremos la tabla de abajo hacia arriba para saber las decisiones
    seleccionados = []
    w_restante = W                                  #---capacidad que va quedando

    for i in range(n, 0, -1):
        #---Si el valor cambió respecto a la fila anterior, este pedido fue incluido
        if dp[i][w_restante] != dp[i - 1][w_restante]:
            pedido = pedidos[i - 1]
            seleccionados.append(pedido)
            w_restante -= discretizar_peso(pedido["peso"])  #---descuenta el peso

    seleccionados.reverse()  #---restaurar el orden original de selección

    #---Calcular totales del resultado
    peso_total  = round(sum(p["peso"]  for p in seleccionados), 2)
    valor_total = round(sum(p["valor"] for p in seleccionados), 2)

    return seleccionados, peso_total, valor_total


def knapsack_memoizacion(pedidos, capacidad_kg):
    #---Capacidad en unidades escaladas
    W = discretizar_peso(capacidad_kg)

    #---Diccionario caché: clave (i, w) → valor máximo calculado
    memo = {}

    def dp(i, w):
        #---Caso base: sin pedidos o sin capacidad → valor 0
        if i == 0 or w == 0:
            return 0.0

        #---Si ya calculamos este subproblema, devolvemos el resultado guardado
        if (i, w) in memo:
            return memo[(i, w)]

        pedido   = pedidos[i - 1]                     #---pedido actual
        w_pedido = discretizar_peso(pedido["peso"])    #---peso escalado
        v_pedido = pedido["valor"]                     #---valor en soles

        #---Opción 1: no incluir el pedido i
        sin_i = dp(i - 1, w)

        #---Opción 2: incluir el pedido i (solo si cabe)
        con_i = 0.0
        if w_pedido <= w:
            con_i = v_pedido + dp(i - 1, w - w_pedido)

        #---Guardamos el mejor de los dos en el caché
        memo[(i, w)] = max(sin_i, con_i)
        return memo[(i, w)]

    #---Disparar la recursión desde el problema completo
    n = len(pedidos)
    dp(n, W)  #---llena el caché

    #---Backtracking: reconstruir los pedidos seleccionados
    seleccionados = []
    w_actual = W

    for i in range(n, 0, -1):
        pedido   = pedidos[i - 1]
        w_pedido = discretizar_peso(pedido["peso"])
        v_pedido = pedido["valor"]

        #---¿Este pedido fue incluido? Comparamos con y sin él
        sin_i = dp(i - 1, w_actual)
        con_i = (v_pedido + dp(i - 1, w_actual - w_pedido)
                 if w_pedido <= w_actual else 0.0)

        if con_i > sin_i:            #---fue incluido
            seleccionados.append(pedido)
            w_actual -= w_pedido     #---descuenta el peso

    seleccionados.reverse()          #---restaurar orden original

    peso_total  = round(sum(p["peso"]  for p in seleccionados), 2)
    valor_total = round(sum(p["valor"] for p in seleccionados), 2)

    return seleccionados, peso_total, valor_total


# ----------------------------------------------------------------
#  IMPRIMIR RESULTADO — formato igual al de greedy.py
# ----------------------------------------------------------------
def imprimir_resultado(metodo, seleccionados, peso_total, valor_total, capacidad_kg):
    print(f"\n{'='*55}")
    print(f"  PROGRAMACIÓN DINÁMICA — {metodo}")
    print(f"{'='*55}")
    print(f"  Capacidad del vehículo : {capacidad_kg:.1f} kg")
    print(f"  Pedidos disponibles    : (ver llamada)")
    print(f"  Pedidos seleccionados  : {len(seleccionados)}")
    print(f"  {'-'*50}")

    for pedido in seleccionados:
        print(f"  ✓ Pedido {pedido['id']:>2} | {pedido['cliente']:<12} "
              f"| Peso: {pedido['peso']:>5.1f} kg "
              f"| Valor: S/ {pedido['valor']:>7.2f}")

    print(f"  {'-'*50}")
    print(f"  Peso total cargado : {peso_total:.2f} kg "
          f"/ {capacidad_kg:.1f} kg")
    print(f"  Valor total        : S/ {valor_total:.2f}")


# ----------------------------------------------------------------
#  Main
# ----------------------------------------------------------------
if __name__ == "__main__":
    nodos   = cargar_nodos()        #---cargamos nodos del grafo de Cusco
    pedidos = cargar_pedidos()      #---cargamos pedidos desde el JSON

    #---Capacidad máxima del vehículo en kilogramos
    capacidad_vehiculo = 30.0       #---ajustar según tu JSON de repartidores

    print(f"\n  Pedidos cargados: {len(pedidos)}")
    print(f"  Capacidad del vehículo: {capacidad_vehiculo} kg")

    #------- MÉTODO 1: Tabulación (bottom-up) -------
    sel_tab, peso_tab, valor_tab = knapsack_tabulacion(
        pedidos, capacidad_vehiculo
    )
    imprimir_resultado("TABULACIÓN (bottom-up)",
                       sel_tab, peso_tab, valor_tab, capacidad_vehiculo)

    #------- MÉTODO 2: Memoización (top-down) -------
    sel_mem, peso_mem, valor_mem = knapsack_memoizacion(
        pedidos, capacidad_vehiculo
    )
    imprimir_resultado("MEMOIZACIÓN (top-down)",
                       sel_mem, peso_mem, valor_mem, capacidad_vehiculo)

    #---Comparación entre métodos
    print(f"\n{'='*55}")
    print(f"  COMPARACIÓN DE MÉTODOS")
    print(f"{'='*55}")
    print(f"  {'Método':<25} {'Pedidos':>7} {'Peso':>10} {'Valor':>12}")
    print(f"  {'-'*50}")
    print(f"  {'Tabulación':<25} {len(sel_tab):>7} "
          f"{peso_tab:>9.2f}kg  S/ {valor_tab:>8.2f}")
    print(f"  {'Memoización':<25} {len(sel_mem):>7} "
          f"{peso_mem:>9.2f}kg  S/ {valor_mem:>8.2f}")
    print(f"{'='*55}")
    print(f"  Ambos métodos deben dar el mismo resultado óptimo.")
    print(f"  Tabulación  → llena toda la tabla  : O(n*W) siempre")
    print(f"  Memoización → solo subproblemas usados: O(n*W) peor caso")

