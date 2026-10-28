"""
analisis.py
Métricas de rendimiento: Quadtree vs. fuerza bruta.
Responde: ¿desde qué tamaño de datos el Quadtree es más rápido?
Las gráficas se guardan en graficas/.

Uso:
    python analisis.py          # benchmark principal
    python analisis.py dimensiones   # rendimiento según la dimensión K
    python analisis.py grande   # tamaños grandes (hasta 100.000 puntos)
    python analisis.py extra    # datos agrupados y capacidad por nodo
"""

import os
import random
import sys
import time

import matplotlib.pyplot as plt

from Quadtreetree import Quadtree, fuerza_bruta_radio, fuerza_bruta_cercano

CIUDAD = 20000                  # metros (20 km x 20 km)
RADIO = 500                     # metros
CARPETA_GRAFICAS = "graficas"
TAMANOS = [10, 25, 50, 100, 200, 500, 1000, 2000, 5000, 10000, 20000]
N_CONSULTAS = 200               # consultas por tamaño, se promedian
REPETICIONES = 3                # se toma la mejor de varias medidas

TAMANOS_GRANDES = [1000, 5000, 10000, 20000, 50000, 100000]
N_CONSULTAS_GRANDE = 50

def generar_puntos(n, semilla):
    rng = random.Random(semilla)
    return [(rng.uniform(0, CIUDAD), rng.uniform(0, CIUDAD)) for _ in range(n)]


#K dimensiones
def generar_puntos_k(n, k, semilla):
    rng = random.Random(semilla)
    return [tuple(rng.uniform(0, CIUDAD) for _ in range(k)) for _ in range(n)]

def medir_dimension(n, k, n_consultas):
    puntos = generar_puntos_k(n, k, 1)
    consultas = generar_puntos_k(n_consultas, k, 2)

    def construir():
        qt = Quadtree((0,) * k, (CIUDAD,) * k, capacidad=8)
        qt.construir(puntos)
        return qt

    t_constr = medir(construir)
    qt = construir()

    t_qt = medir(lambda: [qt.vecino_mas_cercano(c) for c in consultas]) / n_consultas
    t_fb = medir(lambda: [fuerza_bruta_cercano(puntos, c) for c in consultas]) / n_consultas

    return t_constr, qt, t_qt * 1e6, t_fb * 1e6

DIMENSIONES = [2, 3, 4, 5, 6, 8]


def experimento_dimensiones(n=10000, n_consultas=30):
    print(f"\n=== EXPERIMENTO: DIMENSIONES (n={n}, vecino más cercano) ===")
    print(f"{'K':>3} | {'constr (s)':>10} | {'nodos':>8} | {'QT (us)':>9} | "
          f"{'FB (us)':>9} | {'FB/QT':>6}")
    filas = []
    for k in DIMENSIONES:
        t_constr, qt, t_qt, t_fb = medir_dimension(n, k, n_consultas)
        nodos = contar_nodos(qt)
        filas.append({"k": k, "construccion": t_constr, "nodos": nodos,
                      "qt": t_qt, "fb": t_fb})
        print(f"{k:>3} | {t_constr:>10.3f} | {nodos:>8} | {t_qt:>9.1f} | "
              f"{t_fb:>9.1f} | {t_fb / t_qt:>6.1f}")
    return filas



def graficar_dimensiones(filas):
    ks = [f["k"] for f in filas]

    fig, (ax1, ax2) = plt.subplots(1, 2, figsize=(13, 5))

    ax1.plot(ks, [f["qt"] for f in filas], "o-", label="Quadtree")
    ax1.plot(ks, [f["fb"] for f in filas], "s-", label="Fuerza bruta")
    ax1.set_title("Vecino más cercano según la dimensión")
    ax1.set_ylabel("Tiempo por consulta (microsegundos)")
    ax1.legend()

    ax2.plot(ks, [f["fb"] / f["qt"] for f in filas], "o-", color="green")
    ax2.axhline(1, linestyle="--", color="gray")
    ax2.set_title("Cuántas veces más rápido es el Quadtree")
    ax2.set_ylabel("Fuerza bruta / Quadtree")

    for ax in (ax1, ax2):
        ax.set_yscale("log")
        ax.set_xticks(ks)
        ax.set_xlabel("Dimensión (K)")
        ax.grid(True, which="both", alpha=0.3)

    plt.tight_layout()
    plt.savefig(os.path.join(CARPETA_GRAFICAS, "dimensiones.png"), dpi=150)
    plt.close()
    print("Guardada: graficas/dimensiones.png")



### Bloque normal
def medir(funcion):
    """Mejor tiempo (segundos) de varias repeticiones."""
    mejor = float("inf")
    for _ in range(REPETICIONES):
        t0 = time.perf_counter()
        funcion()
        mejor = min(mejor, time.perf_counter() - t0)
    return mejor


def ejecutar_benchmark(tamanos, n_consultas):
    resultados = []
    for n in tamanos:
        puntos = generar_puntos(n, semilla=1)
        consultas = generar_puntos(n_consultas, semilla=2)

        # Construcción del árbol (se paga una sola vez)
        def construir():
            qt = Quadtree((0, 0), (CIUDAD, CIUDAD), capacidad=8)
            qt.construir(puntos)
            return qt
        t_construccion = medir(construir)
        qt = construir()

        # Tiempo promedio POR CONSULTA (en microsegundos)
        t_qt_radio = medir(lambda: [qt.buscar_en_radio(c, RADIO) for c in consultas]) / n_consultas
        t_fb_radio = medir(lambda: [fuerza_bruta_radio(puntos, c, RADIO) for c in consultas]) / n_consultas
        t_qt_cerc = medir(lambda: [qt.vecino_mas_cercano(c) for c in consultas]) / n_consultas
        t_fb_cerc = medir(lambda: [fuerza_bruta_cercano(puntos, c) for c in consultas]) / n_consultas

        fila = {
            "n": n,
            "construccion": t_construccion,
            "qt_radio": t_qt_radio * 1e6,
            "fb_radio": t_fb_radio * 1e6,
            "qt_cercano": t_qt_cerc * 1e6,
            "fb_cercano": t_fb_cerc * 1e6,
        }
        resultados.append(fila)
        print(f"n={n:>6} | radio: QT {fila['qt_radio']:9.1f} us  FB {fila['fb_radio']:9.1f} us"
              f" | cercano: QT {fila['qt_cercano']:9.1f} us  FB {fila['fb_cercano']:9.1f} us")
    return resultados


def punto_de_cruce(resultados, clave_qt, clave_fb):
    """Primer tamaño donde el Quadtree es más rápido (y se mantiene así)."""
    for i, fila in enumerate(resultados):
        if all(r[clave_qt] < r[clave_fb] for r in resultados[i:]):
            return fila["n"]
    return None


def graficar(resultados, sufijo=""):
    ns = [r["n"] for r in resultados]

    fig, (ax1, ax2) = plt.subplots(1, 2, figsize=(14, 6))
    ax1.plot(ns, [r["qt_radio"] for r in resultados], "o-", label="Quadtree")
    ax1.plot(ns, [r["fb_radio"] for r in resultados], "s-", label="Fuerza bruta")
    ax1.set_title(f"Búsqueda por radio ({RADIO} m)")

    ax2.plot(ns, [r["qt_cercano"] for r in resultados], "o-", label="Quadtree")
    ax2.plot(ns, [r["fb_cercano"] for r in resultados], "s-", label="Fuerza bruta")
    ax2.set_title("Vecino más cercano")

    for ax in (ax1, ax2):
        ax.set_xscale("log")
        ax.set_yscale("log")
        ax.set_xlabel("Número de puntos (n)")
        ax.set_ylabel("Tiempo por consulta (microsegundos)")
        ax.grid(True, which="both", alpha=0.3)
        ax.legend()

    plt.tight_layout()
    plt.savefig(os.path.join(CARPETA_GRAFICAS, f"rendimiento_consultas{sufijo}.png"), dpi=150)
    plt.close()

    # Costo de construcción
    plt.figure(figsize=(7, 5))
    plt.plot(ns, [r["construccion"] for r in resultados], "o-", color="purple")
    plt.xscale("log")
    plt.yscale("log")
    plt.xlabel("Número de puntos (n)")
    plt.ylabel("Tiempo de construcción (segundos)")
    plt.title("Costo de construir el Quadtree")
    plt.grid(True, which="both", alpha=0.3)
    plt.tight_layout()
    plt.savefig(os.path.join(CARPETA_GRAFICAS, f"construccion{sufijo}.png"), dpi=150)
    plt.close()
    print(f"Guardadas: rendimiento_consultas{sufijo}.png y construccion{sufijo}.png")


def discusion(resultados):
    cruce_radio = punto_de_cruce(resultados, "qt_radio", "fb_radio")
    cruce_cerc = punto_de_cruce(resultados, "qt_cercano", "fb_cercano")
    print("\n=== RESULTADOS ===")
    print(f"Búsqueda por radio: el Quadtree gana desde n = {cruce_radio}")
    print(f"Vecino más cercano: el Quadtree gana desde n = {cruce_cerc}")
    ultimo = resultados[-1]
    print(f"Con n = {ultimo['n']}: radio es {ultimo['fb_radio'] / ultimo['qt_radio']:.1f}x más rápido, "
          f"cercano {ultimo['fb_cercano'] / ultimo['qt_cercano']:.1f}x más rápido.")

    print("\n=== CONSULTAS NECESARIAS PARA AMORTIZAR LA CONSTRUCCIÓN ===")
    print(f"{'n':>7} | {'construcción (s)':>16} | {'consultas radio':>15} | {'consultas cercano':>17}")
    for r in resultados:
        ahorro_radio = (r["fb_radio"] - r["qt_radio"]) * 1e-6      # segundos ahorrados por consulta
        ahorro_cerc = (r["fb_cercano"] - r["qt_cercano"]) * 1e-6

        def necesarias(ahorro):
            return f"{r['construccion'] / ahorro:.0f}" if ahorro > 0 else "nunca"

        print(f"{r['n']:>7} | {r['construccion']:>16.4f} | "
              f"{necesarias(ahorro_radio):>15} | {necesarias(ahorro_cerc):>17}")
    print("\nNota: el árbol cuesta construirlo; solo conviene si se hacen muchas consultas.")


# =====================================================================
# EXPERIMENTOS EXTRA: datos agrupados y capacidad por nodo
# =====================================================================
CAPACIDADES = [1, 2, 4, 8, 16, 32, 64]


def generar_agrupados(n, semilla, n_zonas=10, sigma=800):
    """Puntos concentrados en zonas densas (barrios, centros comerciales)."""
    rng_c = random.Random(99)       # centros fijos: datos y consultas comparten zonas
    centros = [(rng_c.uniform(2000, CIUDAD - 2000), rng_c.uniform(2000, CIUDAD - 2000))
               for _ in range(n_zonas)]
    rng = random.Random(semilla)
    puntos = []
    while len(puntos) < n:
        cx, cy = rng.choice(centros)
        x, y = rng.gauss(cx, sigma), rng.gauss(cy, sigma)
        if 0 <= x <= CIUDAD and 0 <= y <= CIUDAD:
            puntos.append((x, y))
    return puntos


def construir_arbol(puntos, capacidad=8):
    qt = Quadtree((0, 0), (CIUDAD, CIUDAD), capacidad=capacidad)
    qt.construir(puntos)
    return qt


def contar_nodos(qt):
    return sum(1 for _ in qt.iterar_nodos())


def experimento_agrupados(n=10000):
    print("\n=== EXPERIMENTO: DATOS UNIFORMES vs AGRUPADOS "
          f"(n={n}, capacidad=8) ===")
    res = {}
    for nombre, generador in (("Uniforme", generar_puntos), ("Agrupado", generar_agrupados)):
        puntos = generador(n, 1)
        consultas = generador(N_CONSULTAS, 2)
        t_constr = medir(lambda: construir_arbol(puntos))
        qt = construir_arbol(puntos)

        encontrados = sum(len(qt.buscar_en_radio(c, RADIO)) for c in consultas) / N_CONSULTAS
        res[nombre] = {
            "construccion": t_constr,
            "profundidad": qt.profundidad(),
            "nodos": contar_nodos(qt),
            "encontrados": encontrados,
            "qt_radio": medir(lambda: [qt.buscar_en_radio(c, RADIO) for c in consultas]) / N_CONSULTAS * 1e6,
            "fb_radio": medir(lambda: [fuerza_bruta_radio(puntos, c, RADIO) for c in consultas]) / N_CONSULTAS * 1e6,
            "qt_cercano": medir(lambda: [qt.vecino_mas_cercano(c) for c in consultas]) / N_CONSULTAS * 1e6,
            "fb_cercano": medir(lambda: [fuerza_bruta_cercano(puntos, c) for c in consultas]) / N_CONSULTAS * 1e6,
        }

    print(f"{'':>9} | {'constr (s)':>10} | {'prof':>4} | {'nodos':>6} | {'pts/radio':>9} | "
          f"{'QT radio':>9} | {'FB radio':>9} | {'QT cerc':>8} | {'FB cerc':>8}")
    for nombre, r in res.items():
        print(f"{nombre:>9} | {r['construccion']:>10.3f} | {r['profundidad']:>4} | {r['nodos']:>6} | "
              f"{r['encontrados']:>9.1f} | {r['qt_radio']:>7.1f}us | {r['fb_radio']:>7.1f}us | "
              f"{r['qt_cercano']:>6.1f}us | {r['fb_cercano']:>6.1f}us")

    # Gráfica de barras
    etiquetas = ["Radio", "Vecino más cercano"]
    ancho = 0.2
    fig, ax = plt.subplots(figsize=(9, 5))
    combinaciones = [("Uniforme", "qt"), ("Agrupado", "qt"), ("Uniforme", "fb"), ("Agrupado", "fb")]
    for i, (nombre, clave) in enumerate(combinaciones):
        valores = [res[nombre][f"{clave}_radio"], res[nombre][f"{clave}_cercano"]]
        metodo = "Quadtree" if clave == "qt" else "Fuerza bruta"
        ax.bar([p + i * ancho for p in range(2)], valores, ancho, label=f"{metodo} - {nombre}")
    ax.set_xticks([p + 1.5 * ancho for p in range(2)])
    ax.set_xticklabels(etiquetas)
    ax.set_yscale("log")
    ax.set_ylabel("Tiempo por consulta (microsegundos)")
    ax.set_title(f"Datos uniformes vs agrupados (n = {n})")
    ax.grid(True, axis="y", which="both", alpha=0.3)
    ax.legend(fontsize=8)
    plt.tight_layout()
    plt.savefig(os.path.join(CARPETA_GRAFICAS, "datos_agrupados.png"), dpi=150)
    plt.close()
    print("Guardada: graficas/datos_agrupados.png")


def experimento_capacidad(n=10000):
    print(f"\n=== EXPERIMENTO: CAPACIDAD POR NODO (n={n}, datos uniformes) ===")
    puntos = generar_puntos(n, 1)
    consultas = generar_puntos(N_CONSULTAS, 2)
    filas = []
    for cap in CAPACIDADES:
        t_constr = medir(lambda: construir_arbol(puntos, cap))
        qt = construir_arbol(puntos, cap)
        fila = {
            "cap": cap,
            "construccion": t_constr,
            "profundidad": qt.profundidad(),
            "nodos": contar_nodos(qt),
            "radio": medir(lambda: [qt.buscar_en_radio(c, RADIO) for c in consultas]) / N_CONSULTAS * 1e6,
            "cercano": medir(lambda: [qt.vecino_mas_cercano(c) for c in consultas]) / N_CONSULTAS * 1e6,
        }
        filas.append(fila)
        print(f"capacidad={cap:>3} | constr {fila['construccion']:.3f} s | prof {fila['profundidad']:>2} | "
              f"nodos {fila['nodos']:>6} | radio {fila['radio']:7.1f} us | cercano {fila['cercano']:7.1f} us")

    caps = [f["cap"] for f in filas]
    fig, (ax1, ax2) = plt.subplots(1, 2, figsize=(13, 5))
    ax1.plot(caps, [f["radio"] for f in filas], "o-", label="Radio (500 m)")
    ax1.plot(caps, [f["cercano"] for f in filas], "s-", label="Vecino más cercano")
    ax1.set_ylabel("Tiempo por consulta (microsegundos)")
    ax1.set_title("Consultas según la capacidad")
    ax1.legend()
    ax2.plot(caps, [f["construccion"] for f in filas], "o-", color="purple")
    ax2.set_ylabel("Tiempo de construcción (segundos)")
    ax2.set_title("Construcción según la capacidad")
    for ax in (ax1, ax2):
        ax.set_xscale("log", base=2)
        ax.set_xlabel("Capacidad por nodo")
        ax.grid(True, which="both", alpha=0.3)
    plt.tight_layout()
    plt.savefig(os.path.join(CARPETA_GRAFICAS, "capacidad.png"), dpi=150)
    plt.close()
    print("Guardada: graficas/capacidad.png")



if __name__ == "__main__":
    os.makedirs(CARPETA_GRAFICAS, exist_ok=True)
    if "extra" in sys.argv:
        experimento_agrupados()
        experimento_capacidad()
    elif "grande" in sys.argv:
        resultados = ejecutar_benchmark(TAMANOS_GRANDES, N_CONSULTAS_GRANDE)
        graficar(resultados, "_grande")
    elif "dimensiones" in sys.argv:
        filas = experimento_dimensiones()
        graficar_dimensiones(filas)
    else:
        resultados = ejecutar_benchmark(TAMANOS, N_CONSULTAS)
        graficar(resultados)
        discusion(resultados)


# =====================================================================
# DISCUSIÓN DE RESULTADOS
# (Python 3.13.2, capacidad = 8, radio = 500 m)
# Los tiempos cambian un poco de una corrida a otra; las cifras son
# de una corrida típica y lo importante es la forma de las curvas.
# =====================================================================
#
# 1. ¿Desde qué tamaño gana el Quadtree?
#    Con muy pocos puntos no vale la pena: revisar 10 puntos uno por uno es
#    más barato que recorrer el árbol y calcular distancias a las celdas.
#    En la búsqueda por radio el Quadtree ya gana con 10 puntos, aunque por
#    muy poco. En el vecino más cercano, con 10 puntos gana la fuerza bruta y
#    con 25 gana el Quadtree. Como no medí tamaños entre 10 y 25, el cruce
#    está en ese intervalo.
#
# 2. ¿Cómo crece cada método?
#    La fuerza bruta revisa todos los puntos, así que su tiempo crece igual
#    que n: si hay el doble de puntos, tarda el doble (O(n)). El Quadtree
#    descarta zonas enteras y casi no se entera de que hay más puntos
#    (cercano a O(log n)). En el radio crece un poco más porque, además de
#    buscar, tiene que devolver todos los puntos encontrados: por eso es
#    O(log n + k), donde k es la cantidad de puntos dentro del círculo. Como
#    la ciudad mide siempre lo mismo y se llena de puntos, k aumenta con n.
#    El vecino más cercano devuelve siempre un solo punto, así que casi no sube.
#
# 3. Tamaños grandes (de 1.000 a 100.000 puntos)
#    Con pocos puntos, cada consulta dura unas decenas de microsegundos y la
#    medición tiembla. Por eso repetí el experimento con tamaños más grandes,
#    donde la diferencia entre métodos es enorme y el ruido casi no se nota.
#    Con 100.000 puntos, la fuerza bruta tarda cerca de 175.000 us por consulta,
#    mientras que el Quadtree tarda unos 700 us en radio (más de 200 veces
#    menos) y unos 100 us en vecino más cercano (más de 1.000 veces menos).
#    Al multiplicar n por 100, la fuerza bruta tarda unas 100 veces más; el
#    Quadtree en vecino más cercano, solo 1,5 veces más.
#
# 4. ¿Vale la pena construir el árbol?
#    Construirlo cuesta tiempo (unos 0,2 s con 10.000 puntos), pero ese costo
#    se recupera con muy pocas consultas, entre 4 y 12 para n >= 25 en mis
#    pruebas.
#
# 5. Datos agrupados (10 zonas densas, como barrios)
#    El árbol solo divide una celda cuando se llena. En las zonas densas las
#    celdas se llenan y se dividen muchas veces; en las zonas vacías casi no
#    se dividen. Por eso el árbol queda desbalanceado y la profundidad sube
#    de 7 a 9. El Quadtree tarda más en radio (de 130 a 460 us) porque el
#    círculo ahora encuentra 112 puntos en lugar de 19, y hay que revisarlos
#    y guardarlos. La fuerza bruta no cambia, porque siempre revisa todos los
#    puntos. Aun así, el Quadtree sigue siendo unas 40 veces más rápido en
#    radio y unas 160 en vecino más cercano.
#
# 6. Capacidad por nodo
#    Con capacidad 1 hay una caja por cada punto: el árbol es enorme y se
#    visitan muchísimos nodos. Con capacidad 64 hay pocas cajas, pero cada
#    hoja que toca el círculo se revisa completa, con hasta 64 puntos. Con capacidad 1 fue claramente la peor. Entre 2 y 32 los tiempos son
#    parecidos (la diferencia está dentro del ruido) y con 64 es algo peor.
#    Elegí 8 como un valor intermedio, sin decir que sea el único bueno.
#
# 7. Dimensiones (K = 2 a 8, 10.000 puntos, vecino más cercano)
#    Con más dimensiones los puntos quedan muy dispersos y el árbol casi no
#    puede descartar celdas. En 2D el Quadtree era entre 175 y 270 veces más rápido (según la corrida)
#    que la fuerza bruta; en 6D, unas 15 veces; y en 8D los dos empataron.
#    Además, cada nodo se divide en 2^K hijos, así que con K = 8 el árbol llegó
#    a casi 66.000 nodos, la mayoría vacíos. La fuerza bruta casi no cambia
#    porque siempre revisa los mismos 10.000 puntos. No medí K = 7 ni K > 8,
#    así que el cruce está "alrededor de K = 8" en mi implementación, con mis
#    parámetros (capacidad 8, datos uniformes).
#
# 8. Limitaciones
#    - Los tiempos dependen del computador y cambian entre corridas.
#    - Está escrito en Python puro, que es lento; en un lenguaje compilado el
#      punto de cruce sería otro.
#    - Los datos agrupados se probaron con un solo patrón de zonas.
#    - El cruce en dimensiones salió de una sola corrida y de un solo n.
