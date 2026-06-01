import numpy as np

# Velocidad de la luz en el vacio (m/s)
C = 3e8

# Longitud de onda incidente (m)
LAMBDA_1 = 500e-9  # 500 nm (verde)

# Frecuencia (Hz)
F_1 = C / LAMBDA_1

# Frecuencia angular (rad/s)
OMEGA_1 = 2 * np.pi * F_1

# Numero de onda (rad/m)
K_1 = 2 * np.pi / LAMBDA_1


# ==========================================
# ONDA INCIDENTE
# f(x,t)=A·sin(kx−ωt+φ)
# ==========================================

def onda_incidente(x, t):
    amplitud = 50
    fase = 0

    return amplitud * np.sin(
        K_1 * x
        - OMEGA_1 * t
        + fase
    )


# ==========================================
# ONDA GENERADA EN EL MATERIAL
# g(x,t)=A2·sin(k2x−ω2t+φ2)
# ==========================================

def onda_material(x, t, material):

    # En un medio:
    # lambda_2 = lambda_1 / n

    lambda_2 = LAMBDA_1 / material.n

    # k2 = 2pi / lambda_2

    k_2 = 2 * np.pi / lambda_2

    # La frecuencia NO cambia al entrar al medio
    omega_2 = OMEGA_1

    return material.A2 * np.sin(
        k_2 * x
        - omega_2 * t
        + material.phi2
    )


# ==========================================
# SUPERPOSICION
# r(x,t)=f(x,t)+g(x,t)
# ==========================================

def onda_resultante(x, t, material):

    return (
        onda_incidente(x, t)
        + onda_material(x, t, material)
    )


# ==========================================
# CAMPO ELECTRICO INCIDENTE
# ==========================================

def campo_electrico_incidente(x, t):
    # E0 es la amplitud maxima del campo electrico
    E0 = 50
    fase_inicial = 0

    # de propagacion hacia la derecha (+x)
    return E0 * np.cos(K_1 * x - OMEGA_1 * t + fase_inicial)


# ==========================================
# CAMPO ELECTRICO EN EL MATERIAL
# ==========================================

def campo_electrico_material(x, t, material):
    lambda_2 = LAMBDA_1 / material.n
    k_2 = 2 * np.pi / lambda_2
    omega_2 = OMEGA_1

    # material.A2 actua como el E0_2 (amplitud en el medio)
    # material.phi2 es el phi_E de la formula
    return material.A2 * np.cos(k_2 * x - omega_2 * t + material.phi2)


# ==========================================
# CAMPO ELECTRICO RESULTANTE (Superposicion)
# ==========================================

def campo_electrico_resultante(x, t, material):
    # El principio de superposicion aplica exactamente igual para los campos
    return (
        campo_electrico_incidente(x, t)
        + campo_electrico_material(x, t, material)
    )


# ==========================================
# CAMPO MAGNETICO INCIDENTE
# ==========================================

def campo_magnetico_incidente(x, t):
    E0 = 50  # Amplitud del campo electrico incidente
    fase_inicial = 0

    # En el vacio, la velocidad de la onda es C
    B0 = E0 / C

    return B0 * np.cos(K_1 * x - OMEGA_1 * t + fase_inicial)


# ==========================================
# CAMPO MAGNETICO EN EL MATERIAL
# ==========================================

def campo_magnetico_material(x, t, material):
    lambda_2 = LAMBDA_1 / material.n
    k_2 = 2 * np.pi / lambda_2
    omega_2 = OMEGA_1

    # En el material la velocidad de la luz disminuye: v = C / n
    velocidad_material = C / material.n

    # Usamos la amplitud electrica del material (material.A2)
    # dividida entre la nueva velocidad
    B0_material = material.A2 / velocidad_material

    return B0_material * np.cos(k_2 * x - omega_2 * t + material.phi2)


# ==========================================
# CAMPO MAGNETICO RESULTANTE
# ==========================================

def campo_magnetico_resultante(x, t, material):
    return (
        campo_magnetico_incidente(x, t)
        + campo_magnetico_material(x, t, material)
    )
