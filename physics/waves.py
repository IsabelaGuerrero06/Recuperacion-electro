import numpy as np

# ============================================================
# CONSTANTES FÍSICAS Y ESCALA VISUAL
# ============================================================

# Velocidad de la luz en el vacío (m/s)
C = 3e8

# Amplitud máxima del campo eléctrico incidente (unidades visuales = pixeles)
E0 = 50.0

# Longitud de onda incidente (m)
LAMBDA_1 = 500e-9          # 500 nm — luz verde

# Factor de escala visual: aumenta λ para que sea visible en pantalla
LAMBDA_ESCALA = 10.0
LAMBDA_VISUAL = LAMBDA_1 * LAMBDA_ESCALA

# Frecuencia (Hz) basada en λ visual
F_1 = C / LAMBDA_VISUAL

# Frecuencia angular de la luz incidente  ωl  (rad/s)
OMEGA_L = 2 * np.pi * F_1

# Número de onda  k = 2π/λ  (rad/m)
K_1 = 2 * np.pi / LAMBDA_VISUAL


# ============================================================
# ESCALA VISUAL DE AMPLITUD
# ============================================================
#
# A_x físico = q·E0 / (m·(ωr² − ωl²))  es extremadamente pequeño
# (orden 1e-18 m). Para que sea visible en pantalla, normalizamos:
#
#   A_ref = q·E0 / (m·ωl²)      → amplitud de referencia
#   A_visual = (A_x / A_ref) × 50   → pixeles
#
# Esto preserva la física relativa: cuando ωr → 0, A_visual → 50 px;
# cuando ωr → ωl (resonancia), A_visual → ±∞ (clippeado a ±120 px).
#
# El factor se calcula dinámicamente a partir del átomo.
# ============================================================

def _escalar_amplitud_con_atomo(A_x_fisico, atomo):
    """
    Escala A_x_fisico a pixeles, manteniendo la proporción física.

        A_ref    = q·E0 / (m·ωl²)
        A_visual = (A_x / A_ref) × 50
                 = A_x · m·ωl² / q·E0 · 50

    Clippeado a [-120, 120] para no salir del canvas.
    """
    A_ref = (atomo.q * E0) / (atomo.m * OMEGA_L**2)
    if abs(A_ref) < 1e-50:
        return 0.0
    ratio = A_x_fisico / A_ref
    return float(np.clip(ratio * 50.0, -120.0, 120.0))


# Función pública (usada en UI para mostrar valor)
def _escalar_amplitud(A_x_fisico):
    """Escala genérica (sin átomo). Solo para compatibilidad en UI."""
    return float(np.clip(A_x_fisico * 1e28, -120, 120))


# ============================================================
# AMPLITUD DE OSCILACIÓN DEL ELECTRÓN
# ============================================================
#
#   A_x = q·E0 / (m·(ωr² − ωl²))
#
# ============================================================

def amplitud_oscilacion(atomo):
    """
    Amplitud física de oscilación del electrón.

        A_x = q·E0 / (m·(ωr² − ωl²))

    Retorna el valor físico en metros.
    """
    denominador = atomo.m * (atomo.omega_r**2 - OMEGA_L**2)
    if abs(denominador) < 1e-60:
        denominador = 1e-60
    return (atomo.q * E0) / denominador


def oscilacion_atomo(t, atomo):
    """
    Desplazamiento del electrón en el tiempo.

        x(t) = A_x · cos(ωl·t)
    """
    A_x = amplitud_oscilacion(atomo)
    return A_x * np.cos(OMEGA_L * t)


# ============================================================
# ONDA INCIDENTE
# ============================================================
#
#   f(x,t) = A1 · sin(k·x − ωl·t)
#
# ============================================================

def onda_incidente(x, t):
    """f(x,t) = 50 · sin(k·x − ωl·t)"""
    A1 = 50.0
    return A1 * np.sin(K_1 * x - OMEGA_L * t)


# ============================================================
# ONDA EMITIDA POR EL ÁTOMO
# ============================================================
#
#   g(x,t) = A_x · sin(k·x − ωl·t + φ)
#
#   — misma k y ωl que la incidente (misma frecuencia)
#   — amplitud A_x derivada del modelo de Lorentz
#   — desfase φ propio del átomo
#
# ============================================================

def onda_emitida(x, t, atomo):
    """g(x,t) = A_x · sin(k·x − ωl·t + φ) [unidades visuales]"""
    A_x_fis = amplitud_oscilacion(atomo)
    A_x_vis = _escalar_amplitud_con_atomo(A_x_fis, atomo)
    return A_x_vis * np.sin(K_1 * x - OMEGA_L * t + atomo.phi)


# ============================================================
# ONDA RESULTANTE
# ============================================================
#
#   r(x,t) = f(x,t) + g(x,t)
#
# ============================================================

def onda_resultante(x, t, atomo):
    """r(x,t) = f(x,t) + g(x,t)"""
    return onda_incidente(x, t) + onda_emitida(x, t, atomo)


# ============================================================
# CAMPO ELÉCTRICO
# ============================================================

def campo_electrico_incidente(x, t):
    """E_inc(x,t) = E0·cos(k·x − ωl·t)"""
    return E0 * np.cos(K_1 * x - OMEGA_L * t)


def campo_electrico_emitido(x, t, atomo):
    """E_emit(x,t) = A_x·cos(k·x − ωl·t + φ) [unidades visuales]"""
    A_x_fis = amplitud_oscilacion(atomo)
    A_x_vis = _escalar_amplitud_con_atomo(A_x_fis, atomo)
    return A_x_vis * np.cos(K_1 * x - OMEGA_L * t + atomo.phi)


def campo_electrico_resultante(x, t, atomo):
    """E_res = E_inc + E_emit"""
    return (
        campo_electrico_incidente(x, t)
        + campo_electrico_emitido(x, t, atomo)
    )


# ============================================================
# CAMPO MAGNÉTICO
# ============================================================
#
# B = E / c  (onda plana en el vacío)
#
# ============================================================

def campo_magnetico_incidente(x, t):
    """B_inc(x,t) = (E0/c)·cos(k·x − ωl·t)"""
    return (E0 / C) * np.cos(K_1 * x - OMEGA_L * t)


def campo_magnetico_emitido(x, t, atomo):
    """B_emit(x,t) = (A_x/c)·cos(k·x − ωl·t + φ)"""
    A_x_fis = amplitud_oscilacion(atomo)
    A_x_vis = _escalar_amplitud_con_atomo(A_x_fis, atomo)
    return (A_x_vis / C) * np.cos(K_1 * x - OMEGA_L * t + atomo.phi)


def campo_magnetico_resultante(x, t, atomo):
    """B_res = B_inc + B_emit"""
    return (
        campo_magnetico_incidente(x, t)
        + campo_magnetico_emitido(x, t, atomo)
    )
