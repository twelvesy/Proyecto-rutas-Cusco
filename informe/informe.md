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
En cada ciudad existen características geográficas y urbanas distintas que influyen directamente en la movilidad y en la eficiencia de los servicios de reparto. En el caso de la ciudad del Cusco, su compleja geografía, calles estrechas, pendientes pronunciadas y alta congestión vehicular representan un gran desafío para las empresas de delivery, ya sea de alimentos, encomiendas u otros productos. Frente a esta realidad, las empresas deben responder constantemente preguntas importantes como: ¿qué ruta permitirá llegar más rápido al destino?, ¿qué camino reducirá el consumo de combustible y los costos de transporte?, ¿qué repartidor se encuentra más cerca de un determinado pedido?, ¿qué entrega tiene mayor prioridad?, o ¿qué pedido puede esperar sin afectar la calidad del servicio?

Para que una empresa de reparto pueda optimizar el servicio que brinda y mejorar la gestión de sus actividades logísticas, resulta necesario contar con un sistema inteligente capaz de analizar rutas, priorizar pedidos y asignar eficientemente a los repartidores. Un sistema de este tipo permite reducir tiempos de entrega, minimizar costos operativos y mejorar la satisfacción de los clientes mediante decisiones rápidas y precisas.

Ante esta situación, en el presente proyecto se desarrollará un sistema orientado a la gestión y optimización de rutas de entrega en la ciudad del Cusco. Dicho sistema hará uso de diversos conceptos y técnicas estudiadas en el curso de Programación III, entre las que destacan algoritmos de ordenación y búsqueda, algoritmos greedy, divide y vencerás, programación dinámica y backtracking. Estas herramientas permitirán modelar y resolver problemas relacionados con la selección de rutas óptimas, asignación de pedidos y organización eficiente de entregas.

Asimismo, se utilizará la plataforma OpenStreetMap para obtener datos reales de ubicación geográfica, específicamente la latitud y longitud de 15 puntos estratégicos dentro de la ciudad del Cusco. Con esta información se construirá un grafo que representará las conexiones entre diferentes zonas de la ciudad, permitiendo simular escenarios reales de reparto y evaluar el desempeño de los algoritmos implementados. Finalmente, todo el proyecto será desarrollado en Python.

---

## 2. Estructura del grafo
Para poder estructurar el grafo que nos representa las conexiones de los diferentes lugares en la ciudad del Cusco, utilizamos laplataforma OpenStreetMap de donde obtuvimos la ubicación geográfica de 15 lugares que son los siguientes:


| ID | Nombre               | Latitud      | Longitud      | Zona   |
|----|----------------------|--------------|---------------|---------|
| 1  | Plaza de Armas       | -13.5167674  | -71.9787787   | Centro  |
| 2  | Mercado San Pedro    | -13.5218144  | -71.9823293   | Centro  |
| 3  | San Blas             | -13.5150724  | -71.9744207   | Centro  |
| 4  | La Merced            | -13.5182841  | -71.9797531   | Centro  |
| 5  | Limaqpampa           | -13.5194058  | -71.9735110   | Centro  |
| 6  | San Cristóbal        | -13.5134815  | -71.9797794   | Norte   |
| 7  | Sacsayhuamán         | -13.5089369  | -71.9828849   | Norte   |
| 8  | Av. de la Cultura    | -13.5271607  | -71.9471462   | Sur     |
| 9  | Wanchaq              | -13.5223795  | -71.9665050   | Sur     |
| 10 | Ttio                 | -13.5311611  | -71.9602407   | Sur     |
| 11 | San Sebastián        | -13.5299637  | -71.9372880   | Este    |
| 12 | Huancaro             | -13.5363860  | -71.9803792   | Oeste   |
| 13 | Mercado Molino       | -13.5358002  | -71.9618861   | Oeste   |
| 14 | Belenpampa           | -13.5252381  | -71.9792285   | Oeste   |
| 15 | Terminal Terrestre   | -13.5348979  | -71.9653603   | Oeste   |
| 16 | Qorikancha           | -13.5187741  | -71.9762609   | Centro  |
| 17 | Mercado Wanchaq      | -13.5243590  | -71.9621470   | Sur     |
| 18 | Ovalo Pachacutec     | -13.5176800  | -71.9856200   | Oeste   |
| 19 | Cristo Blanco        | -13.5071500  | -71.9736400   | Norte   |
| 20 | Estadio Garcilaso    | -13.5209800  | -71.9698500   | Centro  |

Tenemos así 20 nodos representando lugares reales del Cusco. La Plaza de Armas será el centro o lugar en el que esta la empresa; ahora, calculamos las distancias y las conexiones entre los nodos para ello se hará el uso dela fórmula Harversine.  

$$
d = 2r \arcsin \left(
\sqrt{
\sin^2\left(\frac{\phi_2 - \phi_1}{2}\right)
+
\cos(\phi_1)\cos(\phi_2)
\sin^2\left(\frac{\lambda_2 - \lambda_1}{2}\right)
}
\right)
$$

donde:  
- $d$: Distancia entre dos puntos.  
- $r$: Radio de la Tierra (6371 km aproximadamente).  
- $\varphi_1$: Latitud del punto 1.  
- $\varphi_2$: Latitud del punto 2.  
- $\lambda_1$: Longitud del punto 1.  
- $\lambda_2$: Longitud del punto 2.  
- $\sin$: Función seno.  
- $\cos$: Función coseno.  
- $\arcsin$: Función arco seno.  

Esta formula nos permite calcular la distancia entre dos puntos sobre la superficie terrestre utilizando sus coordenadas geográficas (latitud y longitud).
Como resultado obtenemos 138 conexiones y que la distancia máxima entre nodos conectados es de 2500 metros. 

Grafo de la Ciudad del Cusco
Información general:

| Característica | Valor |
|---|---|
| Número de nodos | 20 |
| Número de conexiones | 138 |

---

Conexiones por nodo:

| ID | Nodo | Conexiones |
|---|---|---|
| 1 | Plaza de Armas | 15 |
| 2 | Mercado San Pedro | 15 |
| 3 | San Blas | 16 |
| 4 | La Merced | 15 |
| 5 | Limaqpampa | 17 |
| 6 | San Cristóbal | 13 |
| 7 | Sacsayhuamán | 13 |
| 8 | Av. de la Cultura | 6 |
| 9 | Wanchaq | 18 |
| 10 | Ttio | 12 |
| 11 | San Sebastián | 2 |
| 12 | Huancaro | 14 |
| 13 | Mercado Molino | 10 |
| 14 | Belenpampa | 17 |
| 15 | Terminal Terrestre | 14 |
| 16 | Qorikancha | 17 |
| 17 | Mercado Wanchaq | 17 |
| 18 | Ovalo Pachacutec | 14 |
| 19 | Cristo Blanco | 13 |
| 20 | Estadio Garcilaso | 18 |

---

Detalle de aristas:

| Nodo origen | Nodo destino | Distancia |
|---|---|---|
| Plaza de Armas | Mercado San Pedro | 679.9 m |
| Plaza de Armas | San Blas | 507.5 m |
| Plaza de Armas | La Merced | 198.8 m |
| Plaza de Armas | Limaqpampa | 640.6 m |
| Plaza de Armas | San Cristóbal | 381.1 m |
| Plaza de Armas | Sacsayhuamán | 977.4 m |
| Plaza de Armas | Wanchaq | 1466.4 m |
| Plaza de Armas | Huancaro | 2188.3 m |
| Plaza de Armas | Belenpampa | 943.1 m |
| Plaza de Armas | Terminal Terrestre | 2483.7 m |
| Plaza de Armas | Qorikancha | 552.9 m |
| Plaza de Armas | Mercado Wanchaq | 925.7 m |
| Plaza de Armas | Ovalo Pachacutec | 746.6 m |
| Plaza de Armas | Cristo Blanco | 804.2 m |
| Plaza de Armas | Estadio Garcilaso | 1496.8 m |
| Mercado San Pedro | San Blas | 1137.1 m |
| Mercado San Pedro | La Merced | 481.3 m |
| Mercado San Pedro | Limaqpampa | 990.3 m |
| Mercado San Pedro | San Cristóbal | 966.7 m |
| Mercado San Pedro | Sacsayhuamán | 1433.2 m |
| Mercado San Pedro | Wanchaq | 1712.0 m |
| Mercado San Pedro | Huancaro | 1634.0 m |
| Mercado San Pedro | Belenpampa | 507.3 m |
| Mercado San Pedro | Terminal Terrestre | 2341.3 m |
| Mercado San Pedro | Qorikancha | 796.1 m |
| Mercado San Pedro | Mercado Wanchaq | 1119.0 m |
| Mercado San Pedro | Ovalo Pachacutec | 581.3 m |
| Mercado San Pedro | Cristo Blanco | 1437.1 m |
| Mercado San Pedro | Estadio Garcilaso | 1806.2 m |
| San Blas | La Merced | 678.2 m |
| San Blas | Limaqpampa | 491.8 m |
| San Blas | San Cristóbal | 605.8 m |
| San Blas | Sacsayhuamán | 1141.5 m |
| San Blas | Wanchaq | 1180.1 m |
| San Blas | Ttio | 2356.0 m |
| San Blas | Huancaro | 2455.9 m |
| San Blas | Belenpampa | 1244.2 m |
| San Blas | Terminal Terrestre | 2412.3 m |
| San Blas | Qorikancha | 582.3 m |
| San Blas | Mercado Wanchaq | 796.0 m |
| San Blas | Ovalo Pachacutec | 1245.0 m |
| San Blas | Cristo Blanco | 729.4 m |
| San Blas | Estadio Garcilaso | 1156.6 m |
| La Merced | Limaqpampa | 686.3 m |
| La Merced | San Cristóbal | 534.0 m |
| La Merced | Sacsayhuamán | 1093.1 m |
| La Merced | Wanchaq | 1503.0 m |
| La Merced | Huancaro | 2014.0 m |
| La Merced | Belenpampa | 775.3 m |
| La Merced | Terminal Terrestre | 2415.4 m |
| La Merced | Qorikancha | 545.0 m |
| La Merced | Mercado Wanchaq | 928.2 m |
| La Merced | Ovalo Pachacutec | 637.8 m |
| La Merced | Cristo Blanco | 986.0 m |
| La Merced | Estadio Garcilaso | 1555.5 m |
| Limaqpampa | San Cristóbal | 945.1 m |
| Limaqpampa | Sacsayhuamán | 1543.5 m |
| Limaqpampa | Wanchaq | 826.5 m |
| Limaqpampa | Ttio | 1940.8 m |
| Limaqpampa | Huancaro | 2028.9 m |
| Limaqpampa | Mercado Molino | 2214.2 m |
| Limaqpampa | Belenpampa | 895.9 m |
| Limaqpampa | Terminal Terrestre | 1934.9 m |
| Limaqpampa | Qorikancha | 200.3 m |
| Limaqpampa | Mercado Wanchaq | 316.0 m |
| Limaqpampa | Ovalo Pachacutec | 1323.1 m |
| Limaqpampa | Cristo Blanco | 1200.8 m |
| Limaqpampa | Estadio Garcilaso | 869.3 m |
| San Cristóbal | Sacsayhuamán | 606.7 m |
| San Cristóbal | Wanchaq | 1743.2 m |
| San Cristóbal | Belenpampa | 1308.6 m |
| San Cristóbal | Qorikancha | 905.5 m |
| San Cristóbal | Mercado Wanchaq | 1253.9 m |
| San Cristóbal | Ovalo Pachacutec | 785.3 m |
| San Cristóbal | Cristo Blanco | 472.2 m |
| San Cristóbal | Estadio Garcilaso | 1743.0 m |
| Sacsayhuamán | Wanchaq | 2317.4 m |
| Sacsayhuamán | Belenpampa | 1855.2 m |
| Sacsayhuamán | Qorikancha | 1512.3 m |
| Sacsayhuamán | Mercado Wanchaq | 1855.9 m |
| Sacsayhuamán | Ovalo Pachacutec | 1016.2 m |
| Sacsayhuamán | Cristo Blanco | 523.4 m |
| Sacsayhuamán | Estadio Garcilaso | 2297.8 m |
| Av. de la Cultura | Wanchaq | 2159.4 m |
| Av. de la Cultura | Ttio | 1483.9 m |
| Av. de la Cultura | San Sebastián | 1110.4 m |
| Av. de la Cultura | Mercado Molino | 1860.7 m |
| Av. de la Cultura | Terminal Terrestre | 2148.8 m |
| Av. de la Cultura | Estadio Garcilaso | 2113.1 m |
| Wanchaq | Ttio | 1188.3 m |
| Wanchaq | Huancaro | 2162.3 m |
| Wanchaq | Mercado Molino | 1573.6 m |
| Wanchaq | Belenpampa | 1411.8 m |
| Wanchaq | Terminal Terrestre | 1397.5 m |
| Wanchaq | Qorikancha | 962.8 m |
| Wanchaq | Mercado Wanchaq | 595.0 m |
| Wanchaq | Ovalo Pachacutec | 2131.6 m |
| Wanchaq | Cristo Blanco | 1896.9 m |
| Wanchaq | Estadio Garcilaso | 177.8 m |
| Ttio | San Sebastián | 2485.0 m |
| Ttio | Huancaro | 2253.3 m |
| Ttio | Mercado Molino | 545.6 m |
| Ttio | Belenpampa | 2155.8 m |
| Ttio | Terminal Terrestre | 692.1 m |
| Ttio | Qorikancha | 2015.8 m |
| Ttio | Mercado Wanchaq | 1639.5 m |
| Ttio | Estadio Garcilaso | 1270.1 m |
| Huancaro | Mercado Molino | 2000.3 m |
| Huancaro | Belenpampa | 1245.8 m |
| Huancaro | Terminal Terrestre | 1632.0 m |
| Huancaro | Qorikancha | 1880.2 m |
| Huancaro | Mercado Wanchaq | 1856.3 m |
| Huancaro | Ovalo Pachacutec | 2155.8 m |
| Huancaro | Estadio Garcilaso | 2336.3 m |
| Mercado Molino | Belenpampa | 2212.3 m |
| Mercado Molino | Terminal Terrestre | 388.8 m |
| Mercado Molino | Qorikancha | 2244.6 m |
| Mercado Molino | Mercado Wanchaq | 1898.7 m |
| Mercado Molino | Estadio Garcilaso | 1693.1 m |
| Belenpampa | Terminal Terrestre | 1844.3 m |
| Belenpampa | Qorikancha | 708.1 m |
| Belenpampa | Mercado Wanchaq | 870.7 m |
| Belenpampa | Ovalo Pachacutec | 1088.0 m |
| Belenpampa | Cristo Blanco | 1747.0 m |
| Belenpampa | Estadio Garcilaso | 1541.9 m |
| Terminal Terrestre | Qorikancha | 1940.7 m |
| Terminal Terrestre | Mercado Wanchaq | 1620.1 m |
| Terminal Terrestre | Estadio Garcilaso | 1543.7 m |
| Qorikancha | Mercado Wanchaq | 383.5 m |
| Qorikancha | Ovalo Pachacutec | 1168.8 m |
| Qorikancha | Cristo Blanco | 1231.3 m |
| Qorikancha | Estadio Garcilaso | 1030.3 m |
| Mercado Wanchaq | Ovalo Pachacutec | 1545.2 m |
| Mercado Wanchaq | Cristo Blanco | 1514.8 m |
| Mercado Wanchaq | Estadio Garcilaso | 690.9 m |
| Ovalo Pachacutec | Cristo Blanco | 1215.4 m |
| Ovalo Pachacutec | Estadio Garcilaso | 2191.5 m |
| Cristo Blanco | Estadio Garcilaso | 1852.5 m |

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

### Caso de uso
- Selección óptima de pedidos para cargar un vehículo de reparto con capacidad limitada.
- Busca maximizar el valor total de los pedidos transportados sin superar el límite de peso.

### Estrategia
- El problema se modela como una variante del **Knapsack 0/1**.
- Cada pedido tiene un peso y un valor, y la solución selecciona un subconjunto de pedidos.
- Se implementan dos enfoques:
  - **Tabulación (bottom-up)**: construye una tabla DP de tamaño O(n · W)
    donde W es la capacidad de carga escalada.
  - **Memoización (top-down)**: usa recursión con caché para evitar recalcular
    subproblemas ya resueltos.

### Detalles de implementación
- Se escala el peso con un factor `ESCALA = 10` para manejar decimales
  y usar índices enteros en la tabla.
- La función `discretizar_peso(peso_kg)` convierte un peso como 4.5 kg a 45.
- En `knapsack_tabulacion`, la tabla `dp[i][w]` guarda el valor máximo usando
  los primeros `i` pedidos con capacidad `w`.
- En `knapsack_memoizacion`, se usa un diccionario `memo[(i, w)]` para guardar
  resultados parciales y evitar recomputar subproblemas.
- Ambos métodos reconstruyen la solución mediante backtracking sobre las
  decisiones almacenadas.

### Complejidad
- Tiempo: O(n · W), donde `n` es el número de pedidos y `W` la capacidad
  escalada en unidades enteras.
- Espacio: O(n · W) para la estructura de tabla en la versión de tabulación.
- En la práctica, si la capacidad es 30 kg y se escala por 10, `W = 300`.

### Ventajas y limitaciones
- Ventaja: garantiza la solución óptima para la selección de pedidos.
- Limitación: el costo depende de la capacidad total del vehículo, por lo que
  puede crecer rápidamente si la capacidad y la resolución de peso aumentan.

### Resultado esperado
- Ambos métodos deben producir el mismo conjunto óptimo de pedidos.
- El enfoque de tabulación recorre sistemáticamente todos los subproblemas,
  mientras que la memoización solo resuelve los estados realmente usados.

---

## 7. Backtracking (`backtracking.py`)
*(completar cuando termine el módulo)*

---

## 8. Comparación de algoritmos
*(completar al final)*

---

## 9. Conclusiones
*(completar al final)*
