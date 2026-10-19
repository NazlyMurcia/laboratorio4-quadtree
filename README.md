# Laboratorio 4: Quadtree para logística de entregas

Implementación desde cero de un Quadtree (generalizado a K dimensiones) para
responder consultas espaciales sobre 10.000 puntos de entrega, comparado con
fuerza bruta.

## Problema

Dados 10.000 puntos de entrega (x, y) en una ciudad de 20 km × 20 km
(coordenadas en **metros**), responder eficientemente:

- ¿Qué puntos están a un radio de 500 m de una ubicación dada?
- ¿Cuál es el punto de entrega más cercano a una ubicación dada?

## Estructura del repositorio

| Archivo | Contenido |
|---|---|
| `Quadtreetree.py` | Quadtree desde cero + funciones de fuerza bruta |
| `test.py` | Pruebas unitarias y visualizaciones |
| `analisis.py` | Benchmark de rendimiento, experimentos extra y discusión |
| `graficas/` | Imágenes generadas por `test.py` y `analisis.py` |

## Entorno

- Python 3.13.2
- NumPy 2.2.4, Matplotlib 3.10.1 (el árbol no usa ninguna librería de árboles;
  Matplotlib solo se usa para graficar)
- Datos: puntos generados con distribución uniforme y semilla fija, en una
  ciudad de 20 km × 20 km, en metros. Los datos son estáticos.

## Cómo ejecutar

```
pip install numpy matplotlib
python test.py              # pruebas unitarias + gráficas de verificación
python analisis.py          # benchmark principal (tarda unos minutos)
python analisis.py extra    # datos agrupados y capacidad por nodo
```

## Diseño

- **Unidades**: metros. El radio de 500 m es literalmente `radio = 500`.
- **K dimensiones**: cada nodo se divide en 2^K hijos (4 en 2D, 8 en 3D),
  generados con `product((0, 1), repeat=k)`.
- **Capacidad**: cada hoja guarda hasta 8 puntos antes de dividirse.
- **Range search**: se descartan los subárboles cuya caja no toca el círculo
  (distancia mínima del centro a la caja mayor que el radio).
- **Vecino más cercano y k vecinos**: branch and bound; se visitan primero los
  hijos más cercanos y se podan las cajas más lejanas que el mejor resultado
  actual.
- **Profundidad máxima**: evita recursión infinita con puntos duplicados.

## Verificación

Las 10 pruebas unitarias comparan el Quadtree contra fuerza bruta (2D y 3D) y
cubren bordes, duplicados, puntos fuera del rango y radios extremos.

### Búsqueda por radio

![Búsqueda por radio](graficas/busqueda_radio.png)

El círculo de 500 m encierra exactamente los 19 puntos encontrados, el mismo
resultado que da la fuerza bruta. A la derecha se ven las celdas del Quadtree:
son más pequeñas donde hay más puntos.

### Vecinos más cercanos

![Vecinos más cercanos](graficas/vecinos_cercanos.png)

Los 5 vecinos más cercanos (51, 121, 129, 155 y 174 m). El círculo punteado
tiene como radio la distancia al quinto vecino y no deja ningún otro punto
adentro.

## Análisis comparativo

![Rendimiento](graficas/rendimiento_consultas.png)

Tiempo por consulta (µs), promedio de 200 consultas aleatorias, una ejecución
representativa:

| n | Radio QT | Radio FB | Cercano QT | Cercano FB |
|---:|---:|---:|---:|---:|
| 10 | 9,3 | 14,4 | 22,9 | 18,8 |
| 25 | 18,5 | 44,2 | 33,2 | 45,5 |
| 100 | 28,7 | 141,9 | 37,2 | 136,7 |
| 1.000 | 52,3 | 1.772,7 | 76,9 | 1.597,2 |
| 10.000 | 153,1 | 17.802,5 | 96,8 | 16.981,2 |
| 20.000 | 219,7 | 35.184,4 | 102,8 | 34.074,6 |

(QT = Quadtree, FB = fuerza bruta.)

### ¿Desde qué tamaño el Quadtree es más rápido que la fuerza bruta?

- **Radio**: desde unos 25 puntos la ventaja es clara. Con n = 10 también gana,
  pero por muy poco, dentro del ruido de medición.
- **Vecino más cercano**: con n = 10 gana la fuerza bruta; el cruce está entre
  25 y 50 puntos.
- Con 10.000 puntos, el Quadtree es entre 100 y 300 veces más rápido.

### Por qué

La fuerza bruta es O(n): revisa todos los puntos y su tiempo se duplica al
duplicar n. El Quadtree poda regiones enteras y crece cerca de O(log n) más
los puntos devueltos. Con pocos puntos pierde por el costo fijo de la
recursión y del cálculo de distancias a las cajas.

### Costo de construcción

![Construcción](graficas/construccion.png)

Construir el árbol cuesta O(n log n) (unos 0,2 s con 10.000 puntos), pero se
recupera con entre 5 y 16 consultas (5 a 12 para n ≥ 50). Con datos estáticos
y muchas consultas, conviene.

### Datos agrupados (zonas densas)

Se generaron 10.000 puntos concentrados en 10 zonas gaussianas (σ = 800 m) y
se compararon con datos uniformes (`python analisis.py extra`).

| | Profundidad | Nodos | Puntos por radio | QT radio | FB radio | QT cercano | FB cercano |
|---|---:|---:|---:|---:|---:|---:|---:|
| Uniforme | 7 | 3.957 | 18,8 | 138 µs | 18.354 µs | 94,6 µs | 17.468 µs |
| Agrupado | 9 | 3.697 | 112,2 | 418 µs | 18.169 µs | 108,6 µs | 17.398 µs |

![Datos agrupados](graficas/datos_agrupados.png)

El árbol se hace más profundo en zonas densas. El mayor tiempo del Quadtree en
radio se debe sobre todo a que el círculo devuelve más puntos (112 contra 19),
no a la estructura. La fuerza bruta no cambia, y el Quadtree sigue siendo unas
43 veces más rápido en radio y unas 160 en vecino más cercano.

### Capacidad por nodo

![Capacidad](graficas/capacidad.png)

| Capacidad | Construcción | Profundidad | Nodos | Radio | Cercano |
|---:|---:|---:|---:|---:|---:|
| 1 | 0,362 s | 13 | 29.029 | 251 µs | 90 µs |
| 2 | 0,278 s | 10 | 14.541 | 188 µs | 97 µs |
| 4 | 0,220 s | 8 | 7.117 | 145 µs | 81 µs |
| 8 | 0,204 s | 7 | 3.957 | 147 µs | 100 µs |
| 16 | 0,172 s | 6 | 1.493 | 161 µs | 98 µs |
| 32 | 0,159 s | 5 | 1.225 | 173 µs | 99 µs |
| 64 | 0,135 s | 5 | 345 | 239 µs | 123 µs |

Las capacidades muy pequeñas generan árboles profundos con muchos nodos, y las
muy grandes obligan a recorrer muchos puntos por hoja. Entre 4 y 16 el
rendimiento es casi igual; se eligió 8 como valor equilibrado. Las diferencias
en vecino más cercano están dentro del ruido de medición.

### Limitaciones

- Los tiempos varían entre ejecuciones y equipos (por ejemplo, la ventaja con
  n = 20.000 en radio salió entre 160x y 200x en dos corridas).
- Python puro tiene constantes altas; en un lenguaje compilado el punto de
  cruce cambiaría.
- Los datos agrupados se midieron con un solo patrón (10 zonas gaussianas);
  otros patrones podrían dar resultados distintos.

## Uso de inteligencia artificial

Usé Claude (Anthropic) como apoyo durante el laboratorio. La IA propuso la
estructura del proyecto y las decisiones de diseño, y generó borradores del
código del Quadtree, de las pruebas y del benchmark. Yo ejecuté y probé el
código, resolví los problemas de mi entorno, revisé las gráficas, interpreté
los resultados del análisis y puedo explicar el funcionamiento del árbol.