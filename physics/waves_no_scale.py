import numpy as np

# ============================================================
# WAVES_NO_SCALE — Versión sin escala visual
# Modelo de Lorentz usando λ₁ real (500 nm) sin LAMBDA_ESCALA.
# Se usa en el sidebar de cálculos.
# ============================================================

# Velocidad de la luz en el vacío (m/s)
C = 3e8

# Amplitud máxima del campo eléctrico incidente (unidades visuales)
E0 = 50.0

# Longitud de onda incidente REAL (m)
LAMBDA_1 = 500e-9          # 500 nm — luz verde

# Frecuencia (Hz)
F_1 = C / LAMBDA_1

# Frecuencia angular de la luz  ωl  (rad/s)
OMEGA_1 = 2 * np.pi * F_1

# Número de onda  k = 2π/λ  (rad/m)
K_1 = 2 * np.pi / LAMBDA_1


# ============================================================
# AMPLITUD DE OSCILACIÓN DEL ELECTRÓN (sin escala visual)
# ============================================================

def amplitud_oscilacion_real(atomo):
    """
    A_x = q·E0 / (m·(ωr² − ωl²))   — valor físico real.
    """
    denominador = atomo.m * (atomo.omega_r**2 - OMEGA_1**2)
    if abs(denominador) < 1e-40:
        denominador = 1e-40
    return (atomo.q * E0) / denominador


# ============================================================
# ONDA INCIDENTE
# ============================================================

def onda_incidente(x, t):
    """f(x,t) = 50·sin(k·x − ωl·t)"""
    return 50.0 * np.sin(K_1 * x - OMEGA_1 * t)


# ============================================================
# ONDA EMITIDA (Lorentz)
# ============================================================

def onda_emitida(x, t, atomo):
    """g(x,t) = A_x·sin(k·x − ωl·t + φ)"""
    A_x = amplitud_oscilacion_real(atomo)
    return A_x * np.sin(K_1 * x - OMEGA_1 * t + atomo.phi)


# Alias para compatibilidad con el sidebar
def onda_material(x, t, atomo):
    return onda_emitida(x, t, atomo)


# ============================================================
# CAMPO ELÉCTRICO
# ============================================================

def campo_electrico_incidente(x, t):
    """E_inc(x,t) = E0·cos(k·x − ωl·t)"""
    return E0 * np.cos(K_1 * x - OMEGA_1 * t)


def campo_electrico_emitido(x, t, atomo):
    """E_emit(x,t) = A_x·cos(k·x − ωl·t + φ)"""
    A_x = amplitud_oscilacion_real(atomo)
    return A_x * np.cos(K_1 * x - OMEGA_1 * t + atomo.phi)


def campo_electrico_material(x, t, atomo):
    return campo_electrico_emitido(x, t, atomo)


def campo_electrico_resultante(x, t, atomo):
    """E_res = E_inc + E_emit"""
    return (
        campo_electrico_incidente(x, t)
        + campo_electrico_emitido(x, t, atomo)
    )


# ============================================================
# CAMPO MAGNÉTICO
# ============================================================

def campo_magnetico_incidente(x, t):
    """B_inc(x,t) = (E0/c)·cos(k·x − ωl·t)"""
    B0 = E0 / C
    return B0 * np.cos(K_1 * x - OMEGA_1 * t)


def campo_magnetico_emitido(x, t, atomo):
    """B_emit(x,t) = (A_x/c)·cos(k·x − ωl·t + φ)"""
    A_x = amplitud_oscilacion_real(atomo)
    return (A_x / C) * np.cos(K_1 * x - OMEGA_1 * t + atomo.phi)


def campo_magnetico_material(x, t, atomo):
    return campo_magnetico_emitido(x, t, atomo)


def campo_magnetico_resultante(x, t, atomo):
    """B_res = B_inc + B_emit"""
    return (
        campo_magnetico_incidente(x, t)
        + campo_magnetico_emitido(x, t, atomo)
    )
