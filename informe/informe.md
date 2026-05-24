<div align="center">

**Universidad Nacional de San Antonio Abad del Cusco**  

<img src="logo.png" width="150"/>  

**Escuela Profesional de Ingenierìa Informàtica y de sistemas** 

**Asignatura:** Programación III  

**Proyecto:** Sistema de Gestión de Rutas Óptimas en Cusco 

**Docentes:** M.Sc. Boris Chullo Llave  

**Integrantes:**  
Condori Lima Crhistian - 240445  
Díaz Gutierrez Lizardo Ronaldinho - 242105  
Ramos Mamani Yovana - 171952  

**28 de mayo de 2026**
</div>


## 1. Introducción
Sistema que gestiona y optimiza rutas de entrega en la ciudad del Cusco,
aplicando algoritmos de ordenación, búsqueda, greedy, divide y vencerás,
programación dinámica y backtracking.

---

## 2. Estructura del grafo
- 15 nodos representando lugares reales del Cusco
- 69 conexiones calculadas con distancia real (fórmula Haversine)
- Distancia máxima entre nodos conectados: 2500 metros

---

## 3. Ordenación y Búsqueda (`ordenacion.py`)

### Gnome Sort — por prioridad
- T(n) = 8n² + 10n - 3
- O(n²) peor caso
- Ordena pedidos de prioridad 1 (urgente) a 3 (puede esperar)

### Comb Sort — por peso
- T(n) = 11n² + 11n·log₁.₃(n)
- O(n²) peor caso, O(n log n) caso promedio
- Ordena pedidos de menor a mayor peso en kg

### Shell Sort — por valor
- T(n) = 2n² + 9n·log₂(n)
- O(n²) peor caso
- Ordena pedidos de menor a mayor valor en soles

### Búsqueda lineal
- O(n) — búsqueda por ID o nombre de cliente

---

## 4. Algoritmo Greedy (`greedy.py`)

### Caso de uso
Asignación de entregas rápidas en Cusco.

### Estrategia
- **Pedido más cercano**: el repartidor elige siempre el pedido
  cuyo origen esté más cerca de su posición actual.
- **Repartidor más cercano**: ante un pedido urgente, se asigna
  al repartidor más próximo al origen del pedido.

### Complejidad
- O(n²) — por cada pedido pendiente recorre todos los restantes

### Ventaja vs limitación
- Ventaja: decisión inmediata, fácil de implementar
- Limitación: no garantiza la ruta global óptima, ignora prioridades

---

## 5. Divide y Vencerás (`divide_venceras.py`)
*(completar cuando termine el módulo)*

---

## 6. Programación Dinámica (`dinamica.py`)
*(completar cuando termine el módulo)*

---

## 7. Backtracking (`backtracking.py`)
*(completar cuando termine el módulo)*

---

## 8. Comparación de algoritmos
*(completar al final)*

---

## 9. Conclusiones
*(completar al final)*
