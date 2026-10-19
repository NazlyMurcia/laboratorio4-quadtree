"""
test.py
Pruebas unitarias + verificación visual del Quadtree.
Las gráficas se guardan en la carpeta graficas/.
"""

import os
import random
import unittest

import matplotlib.pyplot as plt
from matplotlib.patches import Circle, Rectangle

from Quadtreetree import Quadtree, fuerza_bruta_radio, fuerza_bruta_cercano

CIUDAD = 20000                 # ciudad de 20 km x 20 km, unidades en metros
CARPETA_GRAFICAS = "graficas"


def generar_puntos(n, k=2, semilla=42, lado=CIUDAD):
    rng = random.Random(semilla)
    return [tuple(rng.uniform(0, lado) for _ in range(k)) for _ in range(n)]


# =====================================================================
# PRUEBAS UNITARIAS
# =====================================================================
class TestQuadtree(unittest.TestCase):

    @classmethod
    def setUpClass(cls):
        cls.puntos = generar_puntos(10000)
        cls.qt = Quadtree((0, 0), (CIUDAD, CIUDAD), capacidad=8)
        cls.qt.construir(cls.puntos)

    def test_tamano(self):
        self.assertEqual(self.qt.tamano, 10000)

    def test_radio_coincide_con_fuerza_bruta(self):
        consultas = generar_puntos(100, semilla=7)
        for centro in consultas:
            a = sorted(self.qt.buscar_en_radio(centro, 500))
            b = sorted(fuerza_bruta_radio(self.puntos, centro, 500))
            self.assertEqual(a, b)

    def test_radio_cero_o_vacio(self):
        self.assertEqual(self.qt.buscar_en_radio((10000, 10000), 0), [])

    def test_radio_gigante_trae_todo(self):
        res = self.qt.buscar_en_radio((10000, 10000), 100000)
        self.assertEqual(len(res), 10000)

    def test_cercano_coincide_con_fuerza_bruta(self):
        for q in generar_puntos(100, semilla=11):
            p1, d1 = self.qt.vecino_mas_cercano(q)
            p2, d2 = fuerza_bruta_cercano(self.puntos, q)
            self.assertAlmostEqual(d1, d2)

    def test_k_cercanos_coincide_con_fuerza_bruta(self):
        for q in generar_puntos(50, semilla=13):
            res = self.qt.k_vecinos_mas_cercanos(q, 5)
            esperado = sorted(Quadtree.distancia(p, q) for p in self.puntos)[:5]
            for (_, d), e in zip(res, esperado):
                self.assertAlmostEqual(d, e)

    def test_punto_fuera_del_rango_se_rechaza(self):
        qt = Quadtree((0, 0), (100, 100))
        self.assertFalse(qt.insertar((500, 500)))
        self.assertEqual(qt.tamano, 0)

    def test_punto_en_el_borde(self):
        qt = Quadtree((0, 0), (100, 100))
        self.assertTrue(qt.insertar((100, 100)))
        self.assertTrue(qt.insertar((0, 0)))
        self.assertEqual(qt.tamano, 2)

    def test_puntos_duplicados_no_rompen_el_arbol(self):
        qt = Quadtree((0, 0), (100, 100), capacidad=4)
        for _ in range(50):
            qt.insertar((10, 10))
        self.assertEqual(len(qt.buscar_en_radio((10, 10), 1)), 50)

    def test_arbol_3d(self):
        puntos = generar_puntos(2000, k=3, lado=1000)
        qt = Quadtree((0, 0, 0), (1000, 1000, 1000), capacidad=8)
        qt.construir(puntos)
        for centro in generar_puntos(30, k=3, semilla=5, lado=1000):
            a = sorted(qt.buscar_en_radio(centro, 100))
            b = sorted(fuerza_bruta_radio(puntos, centro, 100))
            self.assertEqual(a, b)
            _, d1 = qt.vecino_mas_cercano(centro)
            _, d2 = fuerza_bruta_cercano(puntos, centro)
            self.assertAlmostEqual(d1, d2)


# =====================================================================
# VISUALIZACIONES
# =====================================================================
def dibujar_hojas(ax, qt, xlim, ylim):
    """Dibuja las cajas de las hojas del árbol que caen en la ventana."""
    for nodo in qt.iterar_nodos():
        if not nodo.es_hoja():
            continue
        x0, y0 = nodo.minimos
        x1, y1 = nodo.maximos
        if x1 < xlim[0] or x0 > xlim[1] or y1 < ylim[0] or y0 > ylim[1]:
            continue
        ax.add_patch(Rectangle((x0, y0), x1 - x0, y1 - y0, fill=False,
                               edgecolor="lightgray", linewidth=0.6))


def puntos_en_ventana(puntos, xlim, ylim):
    return [p for p in puntos
            if xlim[0] <= p[0] <= xlim[1] and ylim[0] <= p[1] <= ylim[1]]


def graficar_radio():
    puntos = generar_puntos(10000)
    qt = Quadtree((0, 0), (CIUDAD, CIUDAD), capacidad=8)
    qt.construir(puntos)

    centro, radio = (10000, 10000), 500
    encontrados = qt.buscar_en_radio(centro, radio)
    conjunto = set(encontrados)

    fig, (ax1, ax2) = plt.subplots(1, 2, figsize=(14, 7))

    # Vista general
    ax1.scatter([p[0] for p in puntos], [p[1] for p in puntos], s=1, c="gray")
    ax1.add_patch(Circle(centro, radio, fill=False, edgecolor="red", linewidth=1.5))
    ax1.scatter([p[0] for p in encontrados], [p[1] for p in encontrados], s=12, c="red")
    ax1.set_title("Vista general (10.000 puntos)")

    # Zoom con subdivisión del árbol
    m = radio * 2.5
    xlim = (centro[0] - m, centro[0] + m)
    ylim = (centro[1] - m, centro[1] + m)
    dibujar_hojas(ax2, qt, xlim, ylim)
    visibles = puntos_en_ventana(puntos, xlim, ylim)
    fuera = [p for p in visibles if p not in conjunto]
    ax2.scatter([p[0] for p in fuera], [p[1] for p in fuera], s=12, c="steelblue",
                label="fuera del radio")
    ax2.scatter([p[0] for p in encontrados], [p[1] for p in encontrados], s=18, c="red",
                label=f"dentro del radio ({len(encontrados)})")
    ax2.add_patch(Circle(centro, radio, fill=False, edgecolor="red", linewidth=1.5))
    ax2.scatter(*centro, marker="x", c="black", s=60, label="centro de consulta")
    ax2.set_xlim(xlim)
    ax2.set_ylim(ylim)
    ax2.set_title(f"Zoom: radio de {radio} m y celdas del Quadtree")
    ax2.legend(loc="upper right", fontsize=8)

    for ax in (ax1, ax2):
        ax.set_aspect("equal")
        ax.set_xlabel("x (metros)")
        ax.set_ylabel("y (metros)")

    plt.tight_layout()
    plt.savefig(os.path.join(CARPETA_GRAFICAS, "busqueda_radio.png"), dpi=150)
    plt.close()
    print("Guardada: graficas/busqueda_radio.png")


def graficar_vecinos(n=5):
    puntos = generar_puntos(10000)
    qt = Quadtree((0, 0), (CIUDAD, CIUDAD), capacidad=8)
    qt.construir(puntos)

    consulta = (7500, 12000)
    cercanos = qt.k_vecinos_mas_cercanos(consulta, n)
    d_max = cercanos[-1][1]
    conjunto = {p for p, _ in cercanos}

    m = d_max * 1.8
    xlim = (consulta[0] - m, consulta[0] + m)
    ylim = (consulta[1] - m, consulta[1] + m)

    fig, ax = plt.subplots(figsize=(8, 8))
    dibujar_hojas(ax, qt, xlim, ylim)
    visibles = puntos_en_ventana(puntos, xlim, ylim)
    otros = [p for p in visibles if p not in conjunto]
    ax.scatter([p[0] for p in otros], [p[1] for p in otros], s=12, c="steelblue")

    ax.add_patch(Circle(consulta, d_max, fill=False, edgecolor="green",
                        linestyle="--", linewidth=1.2))
    for i, (p, d) in enumerate(cercanos):
        ax.plot([consulta[0], p[0]], [consulta[1], p[1]], c="green", linewidth=0.8)
        ax.scatter(*p, c="red", s=40)
        ax.annotate(f"{i + 1}: {d:.0f} m", p, textcoords="offset points",
                    xytext=(6, 6), fontsize=8)

    mas_cercano = cercanos[0][0]
    ax.scatter(*mas_cercano, marker="*", c="gold", edgecolors="black", s=250,
               label="más cercano", zorder=5)
    ax.scatter(*consulta, marker="x", c="black", s=70, label="ubicación dada")

    ax.set_xlim(xlim)
    ax.set_ylim(ylim)
    ax.set_aspect("equal")
    ax.set_xlabel("x (metros)")
    ax.set_ylabel("y (metros)")
    ax.set_title(f"{n} vecinos más cercanos")
    ax.legend(loc="upper right", fontsize=8)

    plt.tight_layout()
    plt.savefig(os.path.join(CARPETA_GRAFICAS, "vecinos_cercanos.png"), dpi=150)
    plt.close()
    print("Guardada: graficas/vecinos_cercanos.png")


if __name__ == "__main__":
    os.makedirs(CARPETA_GRAFICAS, exist_ok=True)
    programa = unittest.main(exit=False, verbosity=2)
    if programa.result.wasSuccessful():
        graficar_radio()
        graficar_vecinos()
    else:
        print("Hay pruebas fallidas: se omiten las gráficas.")