import time
from algoritmos.greedy import greedy_pedido_mas_cercano

#--- DIVIDE Y VENCERÁS (Partición Espacial Recursiva de la Red Vial)
#--- Complejidad Temporal: O(n log n) debido a la ecuación de recurrencia T(n) = 2T(n/2) + O(n) por el cálculo de medianas.
#--- Complejidad Espacial: O(n log n) por el marco de memoria del árbol de recursión y sublistas generadas.
def dividir_zona_geografica(ids_nodos: list, diccionario_nodos: dict, profundidad: int = 0, prof_maxima: int = 2) -> list:
    """
    Subdivide recursivamente el plano cartesiano urbano de Cusco en sectores balanceados,
    utilizando como pivote de corte la mediana del eje coordenado con mayor dispersión.
    """
    # CASO BASE: Si el subgrupo tiene 2 o menos nodos, o alcanzamos el tope de la profundidad, paramos la subdivisión
    if len(ids_nodos) <= 2 or profundidad >= prof_maxima:
        return [ids_nodos] if ids_nodos else []
        
    # Filtramos preventivamente que los IDs existan dentro de la estructura de datos activa
    validos = [uid for uid in ids_nodos if uid in diccionario_nodos]
    if not validos:
        return [ids_nodos]
        
    # Extracción de coordenadas de los nodos válidos
    lats = [diccionario_nodos[uid]["lat"] for uid in validos]
    lons = [diccionario_nodos[uid]["lon"] for uid in validos]
    
    # DIVISIÓN BINARIA EN BASE A EXTENSIÓN: Evaluamos si el plano se estira más en longitud (X) o latitud (Y)
    if (max(lons) - min(lons)) >= (max(lats) - min(lats)):
        lon_media = (max(lons) + min(lons)) / 2  # Punto medio geométrico en X
        # Conquista: Separamos los nodos en subconjunto izquierdo y derecho
        izq = [uid for uid in validos if diccionario_nodos[uid]["lon"] <= lon_media]
        der = [uid for uid in validos if diccionario_nodos[uid]["lon"] > lon_media]
    else:
        lat_media = (max(lats) + min(lats)) / 2  # Punto medio geométrico en Y
        # Conquista: Separamos los nodos en subconjunto superior e inferior
        izq = [uid for uid in validos if diccionario_nodos[uid]["lat"] <= lat_media]
        der = [uid for uid in validos if diccionario_nodos[uid]["lat"] > lat_media]
        
    resultado = []
    # COMBINACIÓN: Llamada recursiva sobre las subzonas incrementando el nivel de profundidad
    for sub_grupo in [izq, der]:
        if sub_grupo:
            resultado.extend(dividir_zona_geografica(sub_grupo, diccionario_nodos, profundidad + 1, prof_maxima))
    return resultado

#--- ORQUESTADOR GENERAL DE LA ZONIFICACIÓN
def procesar_divide_y_venceras(grafo_nx, num_repartidores: int = 3) -> dict:
    """
    Zonifica Cusco mediante particiones geográficas y calcula las sub-rutas de entrega
    para múltiples repartidores usando el resolvedor voraz Greedy.
    """
    inicio_tiempo = time.perf_counter()
    # Generamos un diccionario indexado O(1) de los nodos del grafo NetworkX
    dicc_nodos = {nodo_id: datos for nodo_id, datos in grafo_nx.nodes(data=True)}
    ids_totales = list(dicc_nodos.keys())
    
    # 1. DIVIDE Y VENCERÁS: Invocación del particionador espacial
    sectores = dividir_zona_geografica(ids_totales, dicc_nodos, prof_maxima=2)
    
    # 2. ASIGNACIÓN ROUND-ROBIN: Distribuimos los sectores equitativamente entre los transportes
    asignaciones = {}
    for idx, sector in enumerate(sectores):
        rep_id = (idx % num_repartidores) + 1
        if rep_id not in asignaciones:
            asignaciones[rep_id] = []
        asignaciones[rep_id].extend(sector)
        
    # 3. OPTIMIZACIÓN INDEPENDIENTE: Resolvemos las subrutas internas de cada vehículo
    rutas_finales = {}
    for rep_id, nodos_zona in asignaciones.items():
        if len(nodos_zona) < 2:
            rutas_finales[rep_id] = {"ruta": nodos_zona, "nombres": [dicc_nodos[x]["nombre"] for x in nodos_zona], "distancia_m": 0.0}
            continue
        # Aplicamos Greedy sobre los nodos asignados a cada repartidor autónomo
        res_greedy = greedy_vecino_mas_cercano(grafo_nx, nodos_zona[0], nodos_zona[1:])
        rutas_finales[rep_id] = {
            "ruta": res_greedy["ruta"],
            "nombres": [dicc_nodos[uid]["nombre"] for uid in res_greedy["ruta"]],
            "distancia_m": res_greedy["distancia_m"]
        }
        
    tiempo_ms = (time.perf_counter() - inicio_tiempo) * 1000
    return {
        "zonas": sectores,
        "asignaciones": rutas_finales,
        "tiempo_ms": round(tiempo_ms, 4)
    }
