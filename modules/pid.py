import os
import time
import math

class PIDController:
    def __init__(self, Kp, Ki, Kd, T, sinal_de_controle_MAX, sinal_de_controle_MIN):
        self.Kp = Kp
        self.Ki = Ki
        self.Kd = Kd
        self.T = T 
        self.sinal_de_controle_MAX = sinal_de_controle_MAX
        self.sinal_de_controle_MIN = sinal_de_controle_MIN
        self.referencia = 0.0
        self.erro_total = 0.0
        self.erro_anterior = 0.0
        self.sinal_de_controle = 0.0

    def atualiza_referencia(self, referencia):
        self.referencia = referencia

    def calcula_sinal_de_controle(self, saida_medida):
        erro = self.referencia - saida_medida
        self.erro_total += erro  # Acumula o erro (Termo Integral)

        # Limitar erro_total
        if self.erro_total >= self.sinal_de_controle_MAX:
            self.erro_total = self.sinal_de_controle_MAX
        elif self.erro_total <= self.sinal_de_controle_MIN:
            self.erro_total = self.sinal_de_controle_MIN

        delta_erro = erro - self.erro_anterior  # Diferença entre os erros (Termo Derivativo)

        # PID calcula sinal de controle
        self.sinal_de_controle = (self.Kp * erro +
                                  (self.Ki * self.T) * self.erro_total +
                                  (self.Kd / self.T) * delta_erro)

        # Limitar sinal_de_controle
        if self.sinal_de_controle >= self.sinal_de_controle_MAX:
            self.sinal_de_controle = self.sinal_de_controle_MAX
        elif self.sinal_de_controle <= self.sinal_de_controle_MIN:
            self.sinal_de_controle = self.sinal_de_controle_MIN

        self.erro_anterior = erro

        return self.sinal_de_controle