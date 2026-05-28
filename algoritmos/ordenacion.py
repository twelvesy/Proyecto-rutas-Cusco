import json
import os

_BASE = os.path.dirname(os.path.abspath(__file__))

#---Cargando pedidos desde json
def cargar_pedidos(ruta_json="datos/pedidos.json"):
    with open (ruta_json,"r",encoding="utf-8") as f:
        data = json.load(f)
    return data["pedidos"]

#---Gnome sort por prioridad
#---Prioridad: 1 = urgente, 2 = normal, 3 = puede esperar
def gnome_sort_prioridad(pedidos):
    arreglo = pedidos.copy()
    indice = 0
    n = len(arreglo)
    while indice < n:
        if indice == 0:
            indice += 1
        elif arreglo[indice]["prioridad"] >= arreglo[indice - 1]["prioridad"]:
            indice += 1
        else:
            arreglo[indice], arreglo[indice - 1] = arreglo[indice - 1], arreglo[indice]
            indice -= 1
    return arreglo

#---Comb sort por peso
def comb_sot_peso(pedidos):
    arreglo=pedidos.copy()
    n=len(arreglo)
    brecha=n
    intercambio = True
    while brecha > 1 or intercambio:
        brecha = int(brecha/1.3)
        if brecha<1:
            brecha =1
        intercambio = False
        for i in range(0,n-brecha):
            if arreglo[i]["peso"]>arreglo[i+brecha]["peso"]:
                arreglo[i], arreglo[i+brecha]= arreglo[i+brecha],arreglo[i]
                intercambio = True
    return arreglo

#---Shell sort por valor
def shell_sort_valor(pedidos):
    arreglo = pedidos.copy()
    n = len(arreglo)
    salto = n // 2
    while salto > 0:
        for i in range(salto, n):
            temp = arreglo[i]
            j = i
            while j >= salto and arreglo[j - salto]["valor"] > temp["valor"]:
                arreglo[j] = arreglo[j - salto]
                j -= salto
            arreglo[j] = temp
        salto //= 2
    return arreglo

#---Búsqueda por ID
def buscar_por_id(pedidos, id_buscado):
    for pedido in pedidos:
        if pedido["id"]==id_buscado:
            return pedido
    return None

#---Búsqueda por cliente
def buscar_por_cliente(pedidos, nombre):
    return [p for p in pedidos if nombre.lower() in p["cliente"].lower()]

#---Mostrar pedidos
def mostrar_pedidos(pedidos, titulo="Pedidos"):
    print(f"\n{'='*60}")
    print(f"  {titulo}")
    print(f"{'='*60}")
    for p in pedidos:
        print(f"  {p['id']:<4} {p['cliente']:<12} Prior:{p['prioridad']} Peso:{p['peso']} Valor:{p['valor']}")
#---Main
if __name__ == "__main__":
    pedidos = cargar_pedidos()
    mostrar_pedidos(pedidos, "Pedidos originales")
    mostrar_pedidos(gnome_sort_prioridad(pedidos), "Ordenados por prioridad")
    mostrar_pedidos(comb_sot_peso(pedidos), "Ordenados por peso")
    mostrar_pedidos(shell_sort_valor(pedidos), "Ordenados por valor")
    
