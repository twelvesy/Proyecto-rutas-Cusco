"""
DIVIDE Y VENCERÁS — Segmentación Geográfica de Cusco
=====================================================
Caso de uso: Dividir el mapa de Cusco en zonas para asignar
             una sub-zona a cada repartidor y optimizar su ruta
             interna con un algoritmo Greedy.
 
Relación de recurrencia: T(n) = 2T(n/2) + O(n)  → O(n log n)
"""
 
import time
import sys
import os
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))
 
from datos.grafo_base import cargar_nodos, haversine
 
# Coordenadas de los nodos (se populan al llamar procesar_divide_y_venceras)
UBICACIONES = {}   # {nodo_id: {"lat": float, "lon": float}}
 
 
def dividir_zona(ubicaciones_ids: list, profundidad: int = 0,
                 prof_maxima: int = 2) -> list:
    """
    Divide recursivamente una lista de IDs de nodos en sub-zonas geográficas.
    Estrategia: dividir por el eje de mayor extensión (latitud o longitud).
 
    Complejidad temporal: O(n log n) — T(n) = 2T(n/2) + O(n).
    Complejidad espacial: O(n log n).
    Caso base: <= 2 ubicaciones o profundidad máxima alcanzada.
    """
    if not ubicaciones_ids:
        return []
    if len(ubicaciones_ids) <= 2 or profundidad >= prof_maxima:
        return [ubicaciones_ids]
 
    validas = [uid for uid in ubicaciones_ids if uid in UBICACIONES]
    if not validas:
        return [ubicaciones_ids]
 
    latitudes  = [UBICACIONES[uid]["lat"] for uid in validas]
    longitudes = [UBICACIONES[uid]["lon"] for uid in validas]
    rango_lat  = max(latitudes)  - min(latitudes)
    rango_lon  = max(longitudes) - min(longitudes)
 
    if rango_lon >= rango_lat:
        lon_media = (max(longitudes) + min(longitudes)) / 2
        zona_izq  = [uid for uid in validas if UBICACIONES[uid]["lon"] <= lon_media]
        zona_der  = [uid for uid in validas if UBICACIONES[uid]["lon"] >  lon_media]
    else:
        lat_media = (max(latitudes) + min(latitudes)) / 2
        zona_izq  = [uid for uid in validas if UBICACIONES[uid]["lat"] <= lat_media]
        zona_der  = [uid for uid in validas if UBICACIONES[uid]["lat"] >  lat_media]
 
    resultado = []
    for zona in [zona_izq, zona_der]:
        if zona:
            resultado.extend(dividir_zona(zona, profundidad + 1, prof_maxima))
    return resultado
 
 
def greedy_vecino_mas_cercano(inicio_id: int, resto_ids: list) -> dict:
    """
    Greedy: construye ruta partiendo de inicio_id visitando el nodo más cercano.
    Complejidad: O(k^2) donde k = tamaño de la zona.
    """
    if not resto_ids:
        return {"ruta": [inicio_id], "distancia_m": 0.0}
 
    ruta       = [inicio_id]
    pendientes = list(resto_ids)
    dist_total = 0.0
    pos_actual = inicio_id
 
    while pendientes:
        mejor_id, mejor_dist = None, float("inf")
        for uid in pendientes:
            d = haversine(
                UBICACIONES[pos_actual]["lat"], UBICACIONES[pos_actual]["lon"],
                UBICACIONES[uid]["lat"],        UBICACIONES[uid]["lon"]
            )
            if d < mejor_dist:
                mejor_dist = d
                mejor_id   = uid
        ruta.append(mejor_id)
        dist_total += mejor_dist
        pendientes.remove(mejor_id)
        pos_actual = mejor_id
 
    return {"ruta": ruta, "distancia_m": round(dist_total, 1)}
 
 
def procesar_divide_y_venceras(grafo, num_repartidores: int = 3) -> dict:
    """
    Aplica Divide y Vencerás para zonificar Cusco y asigna ruta a cada repartidor.
    """
    global UBICACIONES
    inicio_tiempo = time.perf_counter()
 
    UBICACIONES = {}
    for nodo_id, datos in grafo.nodes(data=True):
        UBICACIONES[nodo_id] = {"lat": datos["lat"], "lon": datos["lon"]}
 
    todos_los_ids = list(grafo.nodes())
    zonas = dividir_zona(todos_los_ids, profundidad=0, prof_maxima=2)
 
    asignacion_raw = {}
    for idx_zona, zona in enumerate(zonas):
        id_rep = (idx_zona % num_repartidores) + 1
        asignacion_raw.setdefault(id_rep, [])
        asignacion_raw[id_rep].extend(zona)
 
    asignaciones = {}
    for id_rep, locs in asignacion_raw.items():
        if len(locs) < 2:
            asignaciones[id_rep] = {"ruta": locs, "distancia_m": 0.0}
            continue
        resultado_g = greedy_vecino_mas_cercano(locs[0], locs[1:])
        asignaciones[id_rep] = {
            "ruta":        resultado_g["ruta"],
            "distancia_m": resultado_g["distancia_m"]
        }
 
    tiempo_ms = round((time.perf_counter() - inicio_tiempo) * 1000, 4)
 
    return {
        "zonas":            zonas,
        "asignaciones":     asignaciones,
        "num_zonas":        len(zonas),
        "num_repartidores": num_repartidores,
        "tiempo_ms":        tiempo_ms,
        "complejidad":      "O(n log n) división + O(k²) por zona",
        "algoritmo":        "Divide y Vencerás — Segmentación Geográfica"
    }
 
 
if __name__ == "__main__":
    from datos.grafo_base import construir_grafo
    nodos = cargar_nodos()
    G = construir_grafo(nodos, distancia_maxima=2500)
    resultado = procesar_divide_y_venceras(G, num_repartidores=3)
    nodos_dict = {n["id"]: n for n in nodos}
 
    print(f"\n{'='*55}")
    print(f"  DIVIDE Y VENCERÁS — Cusco")
    print(f"{'='*55}")
    print(f"  Zonas: {resultado['num_zonas']}  |  Tiempo: {resultado['tiempo_ms']} ms")
    for id_rep, datos in resultado["asignaciones"].items():
        ruta_nombres = [nodos_dict[uid]["nombre"] for uid in datos["ruta"]]
        print(f"  Rep {id_rep}: {' → '.join(ruta_nombres)}")
        print(f"           Distancia: {datos['distancia_m']} m")
