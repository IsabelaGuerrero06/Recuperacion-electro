import numpy as np

# Velocidad de la luz en el vacío (m/s)
C = 3e8

# Longitud de onda incidente (m)
LAMBDA_1 = 500e-9  # 500 nm (verde)

# Escala visual de longitud de onda
# Mayor valor = onda mas larga en pantalla
LAMBDA_ESCALA = 10.0

LAMBDA_VISUAL = LAMBDA_1 * LAMBDA_ESCALA

# Frecuencia (Hz)
F_1 = C / LAMBDA_VISUAL

# Frecuencia angular (rad/s)
OMEGA_1 = 2 * np.pi * F_1

# Número de onda (rad/m)
K_1 = 2 * np.pi / LAMBDA_VISUAL


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
    # λ₂ = λ₁ / n

    lambda_2 = LAMBDA_VISUAL / material.n

    # k₂ = 2π / λ₂

    k_2 = 2 * np.pi / lambda_2

    # La frecuencia NO cambia al entrar al medio
    omega_2 = OMEGA_1

    return material.A2 * np.sin(
        k_2 * x
        - omega_2 * t
        + material.phi2
    )


# ==========================================
# SUPERPOSICIÓN
# r(x,t)=f(x,t)+g(x,t)
# ==========================================

def onda_resultante(x, t, material):

    return (
        onda_incidente(x, t)
        + onda_material(x, t, material)
    )