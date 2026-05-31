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
#Esa amplitud es para mantener una escala visual
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


# ==========================================
# CAMPO ELÉCTRICO INCIDENTE 
# ==========================================
def campo_electrico_incidente(x, t):
    # E0 es la amplitud máxima del campo eléctrico
    E0 = 50 
    fase_inicial = 0  # phi_E para la onda incidente

    #  Invertimos el orden (k*x - w*t) para mantener la dirección 
    # de propagación hacia la derecha (+x) 
    return E0 * np.cos(K_1 * x - OMEGA_1 * t + fase_inicial)


# ==========================================
# CAMPO ELÉCTRICO EN EL MATERIAL
# ==========================================
def campo_electrico_material(x, t, material):
    lambda_2 = LAMBDA_VISUAL / material.n
    k_2 = 2 * np.pi / lambda_2
    omega_2 = OMEGA_1

    # material.A2 actúa como el E0_2 (amplitud en el medio)
    # material.phi2 es el phi_E de la fórmula 
    return material.A2 * np.cos(k_2 * x - omega_2 * t + material.phi2)


# ==========================================
# CAMPO ELÉCTRICO RESULTANTE (Superposición)
# ==========================================
def campo_electrico_resultante(x, t, material):
    # El principio de superposición aplica exactamente igual para los campos
    return (
        campo_electrico_incidente(x, t) 
        + campo_electrico_material(x, t, material)
    )


# ==========================================
# CAMPO MAGNÉTICO INCIDENTE
# ==========================================
def campo_magnetico_incidente(x, t):
    E0 = 50  # Amplitud del campo eléctrico incidente
    fase_inicial = 0
    
    # En el vacío, la velocidad de la onda es C
    B0 = E0 / C  
    
    return B0 * np.cos(K_1 * x - OMEGA_1 * t + fase_inicial)


# ==========================================
# CAMPO MAGNÉTICO EN EL MATERIAL
# ==========================================
def campo_magnetico_material(x, t, material):
    lambda_2 = LAMBDA_VISUAL / material.n
    k_2 = 2 * np.pi / lambda_2
    omega_2 = OMEGA_1
    
    #  En el material la velocidad de la luz disminuye: v = C / n
    velocidad_material = C / material.n
    
    # Usamos la amplitud eléctrica del material (material.A2) 
    # dividida entre la nueva velocidad
    B0_material = material.A2 / velocidad_material
    
    return B0_material * np.cos(k_2 * x - omega_2 * t + material.phi2)


# ==========================================
# CAMPO MAGNÉTICO RESULTANTE
# ==========================================
def campo_magnetico_resultante(x, t, material):
    return (
        campo_magnetico_incidente(x, t) 
        + campo_magnetico_material(x, t, material)
    )