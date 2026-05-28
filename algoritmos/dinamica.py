"""
PROGRAMACIÓN DINÁMICA — Knapsack 0/1 (Problema de la Mochila)
Tabulación bottom-up: O(n*W) tiempo y espacio.
"""
import time, sys, os
sys.path.insert(0, os.path.join(os.path.dirname(os.path.abspath(__file__)), ".."))
from datos.grafo_base import cargar_nodos
import json

def cargar_pedidos(ruta_json=None):
    if ruta_json is None:
        ruta_json = os.path.join(os.path.dirname(os.path.abspath(__file__)),
                                 "..", "datos", "pedidos.json")
    with open(ruta_json, "r", encoding="utf-8") as f:
        data = json.load(f)
    return data["pedidos"]

ESCALA = 10

def discretizar_peso(peso_kg):
    return round(peso_kg * ESCALA)

def knapsack_tabulacion(pedidos, capacidad_kg):
    n = len(pedidos)
    W = discretizar_peso(capacidad_kg)
    dp = [[0.0] * (W + 1) for _ in range(n + 1)]
    for i in range(1, n + 1):
        pedido   = pedidos[i - 1]
        w_pedido = discretizar_peso(pedido["peso"])
        v_pedido = pedido["valor"]
        for w in range(W + 1):
            dp[i][w] = dp[i - 1][w]
            if w_pedido <= w:
                valor_con = dp[i - 1][w - w_pedido] + v_pedido
                if valor_con > dp[i][w]:
                    dp[i][w] = valor_con
    seleccionados = []
    w_restante = W
    for i in range(n, 0, -1):
        if dp[i][w_restante] != dp[i - 1][w_restante]:
            pedido = pedidos[i - 1]
            seleccionados.append(pedido)
            w_restante -= discretizar_peso(pedido["peso"])
    seleccionados.reverse()
    peso_total  = round(sum(p["peso"]  for p in seleccionados), 2)
    valor_total = round(sum(p["valor"] for p in seleccionados), 2)
    return seleccionados, peso_total, valor_total

def knapsack_memoizacion(pedidos, capacidad_kg):
    W = discretizar_peso(capacidad_kg)
    memo = {}
    def dp(i, w):
        if i == 0 or w == 0:
            return 0.0
        if (i, w) in memo:
            return memo[(i, w)]
        pedido   = pedidos[i - 1]
        w_pedido = discretizar_peso(pedido["peso"])
        v_pedido = pedido["valor"]
        sin_i = dp(i - 1, w)
        con_i = 0.0
        if w_pedido <= w:
            con_i = v_pedido + dp(i - 1, w - w_pedido)
        memo[(i, w)] = max(sin_i, con_i)
        return memo[(i, w)]
    n = len(pedidos)
    dp(n, W)
    seleccionados = []
    w_actual = W
    for i in range(n, 0, -1):
        pedido   = pedidos[i - 1]
        w_pedido = discretizar_peso(pedido["peso"])
        v_pedido = pedido["valor"]
        sin_i = dp(i - 1, w_actual)
        con_i = (v_pedido + dp(i - 1, w_actual - w_pedido) if w_pedido <= w_actual else 0.0)
        if con_i > sin_i:
            seleccionados.append(pedido)
            w_actual -= w_pedido
    seleccionados.reverse()
    peso_total  = round(sum(p["peso"]  for p in seleccionados), 2)
    valor_total = round(sum(p["valor"] for p in seleccionados), 2)
    return seleccionados, peso_total, valor_total

# ── Función principal usada desde la interfaz ──────────────────────
def optimizar_carga_mochila(pedidos, capacidad_kg=15.0) -> dict:
    """
    Ejecuta Knapsack 0/1 (tabulación) y retorna resultado estructurado.
    """
    t0 = time.perf_counter()
    seleccionados, peso_total, valor_total = knapsack_tabulacion(pedidos, capacidad_kg)
    tiempo_ms = round((time.perf_counter() - t0) * 1000, 4)
    return {
        "pedidos_incluidos": seleccionados,
        "peso_total":        peso_total,
        "valor_maximo":      valor_total,
        "capacidad_kg":      capacidad_kg,
        "tiempo_ms":         tiempo_ms,
        "complejidad":       f"O(n × W) = O({len(pedidos)} × {discretizar_peso(capacidad_kg)})",
        "algoritmo":         "Knapsack 0/1 — Tabulación (bottom-up)"
    }

if __name__ == "__main__":
    pedidos = cargar_pedidos()
    resultado = optimizar_carga_mochila(pedidos, 30.0)
    print(f"Valor máximo: S/. {resultado['valor_maximo']}")
    print(f"Peso total:   {resultado['peso_total']} kg")
    print(f"Pedidos:      {len(resultado['pedidos_incluidos'])}")
    print(f"Tiempo:       {resultado['tiempo_ms']} ms")
