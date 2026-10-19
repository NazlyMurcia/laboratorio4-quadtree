"""
Quadtreetree.py
Quadtree (generalizable a K dimensiones) implementado desde cero.
Unidades: metros.
"""

import math
from itertools import product


class Nodo:
    """Región rectangular (hiper-rectángulo en K dim) del espacio."""

    def __init__(self, minimos, maximos, capacidad, profundidad=0, profundidad_max=20):
        self.minimos = minimos            # esquina inferior, ej: (0, 0)
        self.maximos = maximos            # esquina superior, ej: (20000, 20000)
        self.capacidad = capacidad
        self.profundidad = profundidad
        self.profundidad_max = profundidad_max
        self.puntos = []                  # lista de tuplas (coordenadas)
        self.hijos = None                 # None = nodo hoja

    def es_hoja(self):
        return self.hijos is None

    def contiene(self, punto):
        """True si el punto cae dentro de la región del nodo."""
        return all(self.minimos[d] <= punto[d] <= self.maximos[d]
                   for d in range(len(punto)))

    def _dividir(self):
        """Crea 2^K hijos y reparte los puntos actuales entre ellos."""
        k = len(self.minimos)
        centro = tuple((self.minimos[d] + self.maximos[d]) / 2 for d in range(k))
        self.hijos = []

        # product((0,1), repeat=k) genera todas las combinaciones de mitades
        # En 2D: (0,0),(0,1),(1,0),(1,1) -> 4 cuadrantes
        for combo in product((0, 1), repeat=k):
            mins = tuple(self.minimos[d] if combo[d] == 0 else centro[d] for d in range(k))
            maxs = tuple(centro[d] if combo[d] == 0 else self.maximos[d] for d in range(k))
            self.hijos.append(Nodo(mins, maxs, self.capacidad,
                                   self.profundidad + 1, self.profundidad_max))

        # Reubicar los puntos que ya había
        puntos_viejos = self.puntos
        self.puntos = []
        for p in puntos_viejos:
            self._hijo_para(p).insertar(p)

    def _hijo_para(self, punto):
        """Devuelve el hijo donde cae el punto (según qué lado del centro esté)."""
        k = len(self.minimos)
        indice = 0
        for d in range(k):
            centro_d = (self.minimos[d] + self.maximos[d]) / 2
            bit = 1 if punto[d] >= centro_d else 0
            indice = indice * 2 + bit      # coincide con el orden de product()
        return self.hijos[indice]

    def insertar(self, punto):
        if not self.contiene(punto):
            return False

        if self.es_hoja():
            # Si hay espacio, o ya no podemos profundizar más, lo guardamos aquí
            if len(self.puntos) < self.capacidad or self.profundidad >= self.profundidad_max:
                self.puntos.append(punto)
                return True
            self._dividir()

        return self._hijo_para(punto).insertar(punto)


class Quadtree:
    """Interfaz pública del árbol."""

    def __init__(self, minimos, maximos, capacidad=8):
        self.k = len(minimos)
        self.raiz = Nodo(tuple(minimos), tuple(maximos), capacidad)
        self.tamano = 0

    # ---------- Construcción ----------
    def insertar(self, punto):
        punto = tuple(punto)
        if self.raiz.insertar(punto):
            self.tamano += 1
            return True
        return False

    def construir(self, puntos):
        for p in puntos:
            self.insertar(p)

    # ---------- Utilidades de distancia ----------
    @staticmethod
    def distancia(a, b):
        return math.sqrt(sum((a[d] - b[d]) ** 2 for d in range(len(a))))

    @staticmethod
    def distancia_a_caja(punto, nodo):
        """Distancia mínima del punto a la caja del nodo (0 si está dentro)."""
        suma = 0.0
        for d in range(len(punto)):
            if punto[d] < nodo.minimos[d]:
                suma += (nodo.minimos[d] - punto[d]) ** 2
            elif punto[d] > nodo.maximos[d]:
                suma += (punto[d] - nodo.maximos[d]) ** 2
        return math.sqrt(suma)

    # ---------- Range search ----------
    def buscar_en_radio(self, centro, radio):
        """Todos los puntos a distancia <= radio del centro."""
        resultado = []
        self._buscar_radio(self.raiz, tuple(centro), radio, resultado)
        return resultado

    def _buscar_radio(self, nodo, centro, radio, resultado):
        # Poda: si la caja ni toca el círculo, ignoramos todo el subárbol
        if self.distancia_a_caja(centro, nodo) > radio:
            return

        if nodo.es_hoja():
            for p in nodo.puntos:
                if self.distancia(p, centro) <= radio:
                    resultado.append(p)
        else:
            for hijo in nodo.hijos:
                self._buscar_radio(hijo, centro, radio, resultado)

    # ---------- Vecino más cercano ----------
    def vecino_mas_cercano(self, consulta):
        """Devuelve (punto, distancia) del punto más cercano a 'consulta'."""
        mejor = [None, float("inf")]       # lista para poder modificarla en la recursión
        self._buscar_cercano(self.raiz, tuple(consulta), mejor)
        return mejor[0], mejor[1]

    def _buscar_cercano(self, nodo, consulta, mejor):
        # Poda: si esta caja está más lejos que el mejor actual, no vale la pena
        if self.distancia_a_caja(consulta, nodo) >= mejor[1]:
            return

        if nodo.es_hoja():
            for p in nodo.puntos:
                dist = self.distancia(p, consulta)
                if dist < mejor[1]:
                    mejor[0], mejor[1] = p, dist
        else:
            # Visitar primero los hijos más cercanos para podar más rápido
            hijos_ordenados = sorted(nodo.hijos,
                                     key=lambda h: self.distancia_a_caja(consulta, h))
            for hijo in hijos_ordenados:
                self._buscar_cercano(hijo, consulta, mejor)

    # ---------- k vecinos más cercanos ----------
    def k_vecinos_mas_cercanos(self, consulta, n):
        """Los n puntos más cercanos, ordenados por distancia."""
        consulta = tuple(consulta)
        # 'mejores' es una lista ordenada de (distancia, punto), máximo n elementos
        mejores = []
        self._buscar_k_cercanos(self.raiz, consulta, n, mejores)
        return [(p, d) for d, p in mejores]

    def _buscar_k_cercanos(self, nodo, consulta, n, mejores):
        cota = mejores[-1][0] if len(mejores) == n else float("inf")
        if self.distancia_a_caja(consulta, nodo) >= cota:
            return

        if nodo.es_hoja():
            for p in nodo.puntos:
                mejores.append((self.distancia(p, consulta), p))
            mejores.sort()
            del mejores[n:]                # nos quedamos solo con los n mejores
        else:
            for hijo in sorted(nodo.hijos,
                               key=lambda h: self.distancia_a_caja(consulta, h)):
                self._buscar_k_cercanos(hijo, consulta, n, mejores)

    # ---------- Info para analizar / graficar ----------
    def iterar_nodos(self):
        """Recorre todos los nodos (útil para dibujar la subdivisión)."""
        pila = [self.raiz]
        while pila:
            nodo = pila.pop()
            yield nodo
            if not nodo.es_hoja():
                pila.extend(nodo.hijos)

    def profundidad(self):
        return max(n.profundidad for n in self.iterar_nodos())


# ---------- Fuerza bruta (para comparar) ----------
def fuerza_bruta_radio(puntos, centro, radio):
    return [p for p in puntos if Quadtree.distancia(p, centro) <= radio]


def fuerza_bruta_cercano(puntos, consulta):
    mejor, mejor_d = None, float("inf")
    for p in puntos:
        d = Quadtree.distancia(p, consulta)
        if d < mejor_d:
            mejor, mejor_d = p, d
    return mejor, mejor_d