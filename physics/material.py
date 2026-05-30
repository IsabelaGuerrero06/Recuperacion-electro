class Material:

    def __init__(
        self,
        nombre,
        indice_refraccion,
        amplitud_generada,
        fase
    ):

        self.nombre = nombre

        self.n = indice_refraccion

        self.A2 = amplitud_generada

        self.phi2 = fase