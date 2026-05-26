import json
import networkx as nx
import math
import os

_BASE = os.path.dirname(os.path.abspath(__file__))
#---Leer nodos desde el JSON
def cargar_nodos(ruta_json="datos/nodos_cusco.json"):
    if ruta_json is None:
        ruta_json = os.path.join(_BASE, "nodos_cusco.json")
    with open(ruta_json, "r", encoding="utf-8") as f:
        data = json.load(f)
    return data["nodos"]

#---Calculamos distancia real entre dos puntos (fórmula Haversine)
def haversine(lat1, lon1, lat2, lon2):
    R = 6371000  #---radio de la Tierra en metros
    phi1, phi2 = math.radians(lat1), math.radians(lat2)
    dphi = math.radians(lat2 - lat1)
    dlambda = math.radians(lon2 - lon1)
    a = math.sin(dphi/2)**2 + math.cos(phi1)*math.cos(phi2)*math.sin(dlambda/2)**2
    return R * 2 * math.atan2(math.sqrt(a), math.sqrt(1 - a))

#---Construimos el grafo conectando nodos cercanos
def construir_grafo(nodos, distancia_maxima=2500):
    G = nx.Graph()

    #---Agregando nodos
    for nodo in nodos:
        G.add_node(nodo["id"],
                   nombre=nodo["nombre"],
                   lat=nodo["lat"],
                   lon=nodo["lon"],
                   zona=nodo["zona"])

    #---Agregando aristas entre nodos dentro del rango
    for i in range(len(nodos)):
        for j in range(i + 1, len(nodos)):
            n1, n2 = nodos[i], nodos[j]
            dist = haversine(n1["lat"], n1["lon"], n2["lat"], n2["lon"])
            if dist <= distancia_maxima:
                G.add_edge(n1["id"], n2["id"],
                           peso=round(dist, 2),
                           calle=f"{n1['nombre']} ↔ {n2['nombre']}")
    return G

#---Mostrar resumen del grafo 
def mostrar_resumen(G):
    print(f"\n{'='*45}")
    print(f"  GRAFO DE CUSCO")
    print(f"{'='*45}")
    print(f"  Nodos    : {G.number_of_nodes()}")
    print(f"  Conexiones: {G.number_of_edges()}")
    print(f"{'='*45}")
    print("\n  Conexiones por nodo:")
    for nodo_id, datos in G.nodes(data=True):
        vecinos = list(G.neighbors(nodo_id))
        print(f"  [{nodo_id:2}] {datos['nombre']:<22} → {len(vecinos)} conexiones")
    print(f"\n  Detalle de aristas (distancia en metros):")
    for u, v, datos in G.edges(data=True):
        n1 = G.nodes[u]["nombre"]
        n2 = G.nodes[v]["nombre"]
        print(f"  {n1:<22} ↔ {n2:<22} : {datos['peso']:>8.1f} m")

#---Main
if __name__ == "__main__":
    nodos = cargar_nodos()
    G = construir_grafo(nodos, distancia_maxima=2500)
    mostrar_resumen(G)
