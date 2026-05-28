import sys, os
sys.path.insert(0, os.path.join(os.path.dirname(os.path.abspath(__file__)), ".."))

from datos.grafo_base import cargar_nodos, haversine
import json

def cargar_pedidos(ruta_json=None):
    if ruta_json is None:
        ruta_json = os.path.join(os.path.dirname(os.path.abspath(__file__)),
                                 "..", "datos", "pedidos.json")
    with open(ruta_json, "r", encoding="utf-8") as f:
        data = json.load(f)
    return data["pedidos"]

def greedy_pedido_mas_cercano(repartidor_lat, repartidor_lon, pedidos, nodos):
    """
    Greedy: el repartidor elige siempre el pedido más cercano a su posición actual.
    Complejidad: O(n²)
    """
    nodos_dict = {n["id"]: n for n in nodos}
    pendientes = pedidos.copy()
    ruta = []
    pos_lat = repartidor_lat
    pos_lon = repartidor_lon

    while pendientes:
        mejor = None
        menor_dist = float("inf")
        for pedido in pendientes:
            nodo_origen = nodos_dict.get(pedido["origen"])
            if not nodo_origen:
                continue
            dist = haversine(pos_lat, pos_lon, nodo_origen["lat"], nodo_origen["lon"])
            if dist < menor_dist:
                menor_dist = dist
                mejor = pedido
        if mejor is None:
            break
        ruta.append(mejor)
        nodo_destino = nodos_dict.get(mejor["destino"])
        if nodo_destino:
            pos_lat = nodo_destino["lat"]
            pos_lon = nodo_destino["lon"]
        pendientes.remove(mejor)

    return ruta

def greedy_repartidor_mas_cercano(pedido_urgente, repartidores, nodos):
    """
    Greedy: asignar pedido urgente al repartidor más cercano.
    Retorna (mejor_repartidor, distancia_minima).
    Complejidad: O(r) donde r = número de repartidores
    """
    nodos_dict = {n["id"]: n for n in nodos}
    nodo_pedido = nodos_dict.get(pedido_urgente["origen"])
    if not nodo_pedido:
        return None, float("inf")

    mejor_repartidor = None
    menor_dist = float("inf")
    for rep in repartidores:
        dist = haversine(rep["lat"], rep["lon"],
                         nodo_pedido["lat"], nodo_pedido["lon"])
        if dist < menor_dist:
            menor_dist = dist
            mejor_repartidor = rep

    return mejor_repartidor, menor_dist

if __name__ == "__main__":
    nodos = cargar_nodos()
    pedidos = cargar_pedidos()
    repartidores = [
        {"nombre": "Repartidor 1", "lat": -13.5170, "lon": -71.9787},
        {"nombre": "Repartidor 2", "lat": -13.5300, "lon": -71.9600},
        {"nombre": "Repartidor 3", "lat": -13.5250, "lon": -71.9820},
    ]
    plaza = next(n for n in nodos if n["id"] == 1)
    ruta = greedy_pedido_mas_cercano(plaza["lat"], plaza["lon"], pedidos[:6], nodos)
    print("Ruta greedy:", [p["id"] for p in ruta])
    pedido_urgente = next(p for p in pedidos if p["prioridad"] == 1)
    rep, dist = greedy_repartidor_mas_cercano(pedido_urgente, repartidores, nodos)
    print(f"Asignado a: {rep['nombre']} ({dist:.1f} m)")
