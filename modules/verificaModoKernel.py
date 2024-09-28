import os
import variables

def verifica_modo_kernel():
    if os.path.exists(variables.arquivo_sensor1_KERNEL_MODE) or os.path.exists(variables.arquivo_sensor2_KERNEL_MODE):
        variables.tipoI2c = 2   
    else:
        variables.tipoI2c = 1
