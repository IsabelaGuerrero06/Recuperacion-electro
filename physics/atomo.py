import numpy as np

# ============================================================
# MODELO DE LORENTZ — Oscilador armónico forzado
# ============================================================
#
# Física:
#   Un electrón ligado al átomo actúa como oscilador armónico.
#   El campo eléctrico incidente ejerce una fuerza F = qE sobre
#   el electrón, que oscila con amplitud:
#
#       A_x = qE0 / (m * (ωr² - ωl²))
#
#   donde:
#       q  = carga del electrón (C)
#       E0 = amplitud máxima del campo eléctrico incidente (unidades visuales)
#       m  = masa del electrón (kg)
#       ωr = frecuencia natural de resonancia = √(k/m)  (rad/s)
#       ωl = frecuencia angular de la luz incidente (rad/s)
#
#   La carga acelerada re-emite radiación (onda secundaria):
#
#       g(x,t) = A_x · sin(kx − ωl·t + φ)
#
# ============================================================


class Atomo:
    """
    Modelo microscópico del átomo según Lorentz.

    Parámetros
    ----------
    nombre            : str    — nombre del átomo/elemento
    masa              : float  — masa del electrón ligado (kg)
    carga             : float  — carga del electrón (C)
    constante_elastica: float  — constante elástica de la ligadura (N/m)
    """

    def __init__(
        self,
        nombre,
        masa,
        carga,
        constante_elastica,
    ):
        self.nombre = nombre

        # Parámetros del oscilador
        self.m = masa                   # kg
        self.q = carga                  # C
        self.k = constante_elastica     # N/m

        # Frecuencia natural de resonancia: ωr = √(k/m)
        self.omega_r = np.sqrt(
            self.k / self.m
        )

    def set_k(self, constante_elastica):
        """
        Actualiza la constante elástica y recalcula la frecuencia de resonancia.
        
        Parámetros
        ----------
        constante_elastica : float
            Nueva constante elástica (N/m)
        """
        self.k = constante_elastica
        self.omega_r = np.sqrt(self.k / self.m)

    def __repr__(self):
        return (
            f"Atomo(nombre={self.nombre!r}, "
            f"m={self.m:.3e}, q={self.q:.3e}, "
            f"k={self.k:.3e}, ωr={self.omega_r:.3e})"
        )
