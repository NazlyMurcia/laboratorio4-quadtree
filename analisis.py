"""
analisis.py
Métricas de rendimiento: Quadtree vs. fuerza bruta.
Responde: ¿desde qué tamaño de datos el Quadtree es más rápido?
Las gráficas se guardan en graficas/.

Uso:
    python analisis.py          # benchmark principal
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


def generar_puntos(n, semilla):
    rng = random.Random(semilla)
    return [(rng.uniform(0, CIUDAD), rng.uniform(0, CIUDAD)) for _ in range(n)]


def medir(funcion):
    """Mejor tiempo (segundos) de varias repeticiones."""
    mejor = float("inf")
    for _ in range(REPETICIONES):
        t0 = time.perf_counter()
        funcion()
        mejor = min(mejor, time.perf_counter() - t0)
    return mejor


def ejecutar_benchmark():
    resultados = []
    for n in TAMANOS:
        puntos = generar_puntos(n, semilla=1)
        consultas = generar_puntos(N_CONSULTAS, semilla=2)

        # Construcción del árbol (se paga una sola vez)
        def construir():
            qt = Quadtree((0, 0), (CIUDAD, CIUDAD), capacidad=8)
            qt.construir(puntos)
            return qt
        t_construccion = medir(construir)
        qt = construir()

        # Tiempo promedio POR CONSULTA (en microsegundos)
        t_qt_radio = medir(lambda: [qt.buscar_en_radio(c, RADIO) for c in consultas]) / N_CONSULTAS
        t_fb_radio = medir(lambda: [fuerza_bruta_radio(puntos, c, RADIO) for c in consultas]) / N_CONSULTAS
        t_qt_cerc = medir(lambda: [qt.vecino_mas_cercano(c) for c in consultas]) / N_CONSULTAS
        t_fb_cerc = medir(lambda: [fuerza_bruta_cercano(puntos, c) for c in consultas]) / N_CONSULTAS

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


def graficar(resultados):
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
    plt.savefig(os.path.join(CARPETA_GRAFICAS, "rendimiento_consultas.png"), dpi=150)
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
    plt.savefig(os.path.join(CARPETA_GRAFICAS, "construccion.png"), dpi=150)
    plt.close()
    print("Guardadas: rendimiento_consultas.png y construccion.png")


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
    else:
        resultados = ejecutar_benchmark()
        graficar(resultados)
        discusion(resultados)


# =====================================================================
# DISCUSIÓN DE RESULTADOS (Python 3.13.2, capacidad=8, radio=500 m)
# Los tiempos varían entre ejecuciones; las cifras son de una corrida típica.
# =====================================================================
# 1. Punto de cruce: el Quadtree supera a la fuerza bruta desde ~25 puntos en
#    búsqueda por radio y entre 25 y 50 puntos en vecino más cercano. Con
#    n = 10 gana por muy poco en radio (dentro del ruido) y pierde en vecino
#    más cercano, porque el costo fijo de la recursión y la poda supera al de
#    recorrer pocos puntos.
# 2. Escalamiento: la fuerza bruta es O(n) (el tiempo se duplica al duplicar n).
#    El Quadtree crece cercano a O(log n) + k (k = puntos devueltos).
#    Con n = 20.000 es ~160-200x más rápido en radio y ~330x en vecino más
#    cercano.
# 3. Amortización: construir el árbol cuesta O(n log n), pero se recupera con
#    entre 5 y 16 consultas (5 a 12 para n >= 50). Con datos estáticos conviene.
# 4. Datos agrupados (10 zonas gaussianas, sigma = 800 m): el árbol sube de
#    profundidad 7 a 9. El Quadtree tarda más en radio (138 -> 418 us) porque
#    el círculo devuelve 112 puntos en lugar de 19, no por la estructura. La
#    fuerza bruta no cambia. Sigue siendo ~43x más rápido en radio y ~160x en
#    vecino más cercano.
# 5. Capacidad por nodo: capacidades 1-2 generan árboles profundos con muchos
#    nodos; 64 obliga a recorrer demasiados puntos por hoja. Entre 4 y 16 el
#    rendimiento es casi igual; se eligió 8. Las diferencias en vecino más
#    cercano están dentro del ruido de medición.
# 6. Limitaciones: los tiempos varían entre ejecuciones y equipos; Python puro
#    tiene constantes altas; los datos agrupados se midieron con un solo patrón.