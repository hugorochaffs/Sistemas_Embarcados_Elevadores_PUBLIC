
from time import sleep
import math
import variables
import verificaModoKernel
import os

def ler_arquivo(caminho):
    try:
        with open(caminho, 'r') as arquivo:
            return arquivo.read().strip()
    except IOError:
        print(f"Não foi possível ler o arquivo: {caminho}")
        return None

def obter_temperatura(caminho):
    try:
        # Tenta ler o arquivo de temperatura
        dado = ler_arquivo(os.path.join(caminho, "in_temp_input"))
        
        if dado:
            try:
                # Converte o dado para float e calcula a temperatura
                temperatura = math.floor((((float(dado) / 1000.0) * 100) + 0.5)) / 100
                return round(temperatura, 2)
            except ValueError as e:
                print(f"Erro ao converter dado para float: {e}")
                return 0
        else:
            return 0
    except Exception as e:
        print(f"Erro ao obter a temperatura: {e}")
        return 0

def configuraI2c():
    verificaModoKernel.verifica_modo_kernel()
    if variables.tipoI2c == 1:  # VERIFICA SE ESTÁ NO MODO NORMAL (1) OU KERNEL (2)
        try:
            from smbus2 import SMBus
        except ImportError:
            print("Erro: A biblioteca 'smbus2' não está instalada. Instale-a com 'pip install smbus2'.")
            return

        try:
            from bmp280 import BMP280
        except ImportError:
            print("Erro: A biblioteca 'bmp280' não está instalada. Instale-a com 'pip install bmp280'.")
            return

        # Se as bibliotecas foram importadas com sucesso, configure os objetos I2C
        try:
            variables.ponteiro_busI2c = SMBus(variables.endereco_busI2c_NORMAL_MODE)
            variables.objBmp280_E1 = BMP280(i2c_dev=variables.ponteiro_busI2c, i2c_addr=variables.endereco_sensorTemp1_NORMAL_MODE)
            variables.objBmp280_E2 = BMP280(i2c_dev=variables.ponteiro_busI2c, i2c_addr=variables.endereco_sensorTemp2_NORMAL_MODE)
        except Exception as e:
            print(f"Erro ao configurar I2C: {e}")
            return



def leTemperaturaSensor(sensor):
    if(variables.tipoI2c == 1):
        if(sensor == 1):
            try:
                temperatura = variables.objBmp280_E1.get_temperature()
                return round(temperatura, 2)
            except NameError:
                print("O sensor bmp280_sensor1 não está definido.")
                return 0
        elif(sensor == 2):
            try:
                temperatura = variables.objBmp280_E2.get_temperature()
                return round(temperatura, 2)
            except NameError:
                print("O sensor bmp280_sensor2 não está definido.")
                return 0
    elif(variables.tipoI2c == 2):
        if(sensor == 1):
            return round(obter_temperatura(variables.arquivo_sensor1_KERNEL_MODE), 2)
        elif(sensor == 2):
            return round(obter_temperatura(variables.arquivo_sensor2_KERNEL_MODE), 2)

def fechaBus():
    if(variables.tipoI2c == 1):
        try:
            variables.ponteiro_busI2c.close()
        except NameError:
            print("O bus i2c não está definido.")
            return None
        
        print("Barramento I2C fechado.")

