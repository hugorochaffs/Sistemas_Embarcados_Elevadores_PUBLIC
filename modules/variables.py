matricula = 6925
arquivo_config_gpio = "gpioConfig.json"
tipoI2c = 1 # TIPO 1 NORMAL, via biblioteca comum. Tipo 2, via KERNEL
arquivo_sensor1_KERNEL_MODE = '/sys/bus/i2c/devices/i2c-1/1-0076/iio:device0/'
arquivo_sensor2_KERNEL_MODE = '/sys/bus/i2c/devices/i2c-1/1-0077/iio:device1/'
ponteiro_busI2c = None
endereco_busI2c_NORMAL_MODE = 1
endereco_sensorTemp1_NORMAL_MODE =0x76  
endereco_sensorTemp2_NORMAL_MODE =0x77
objBmp280_E1 = None
objBmp280_E2 = None
hostname = None
emergencia_E1 = 0
emergencia_E2 = 0
#VERIFICA SE HOUVE DESLOCAMENTO [INICIAL, FINAL]
deslocamento_E1 = [0,0]
deslocamento_E2 = [0,0]
verificadoErro_E1 = 0
verificadoErro_E2 = 0
useOled = False

listaBotoesE1 = [
    {"endereco": 0x00, "status": 0},#ˆT
    {"endereco": 0x01, "status": 0},#v1
    {"endereco": 0x02, "status": 0},#ˆ1
    {"endereco": 0x03, "status": 0},#v2
    {"endereco": 0x04, "status": 0},#ˆ2
    {"endereco": 0x05, "status": 0},#v3
    {"endereco": 0x06, "status": 0},#emergencia
    {"endereco": 0x07, "status": 0},#terreo
    {"endereco": 0x08, "status": 0},#1andar
    {"endereco": 0x09, "status": 0},#2andar
    {"endereco": 0x0A, "status": 0}#3andar
]
listaBotoesE2 = [
    {"endereco": 0xA0, "status": 0},#ˆT
    {"endereco": 0xA1, "status": 0},#v1
    {"endereco": 0xA2, "status": 0},#ˆ1
    {"endereco": 0xA3, "status": 0},#v2
    {"endereco": 0xA4, "status": 0},#ˆ2
    {"endereco": 0xA5, "status": 0},#v3
    {"endereco": 0xA6, "status": 0},#emergencia
    {"endereco": 0xA7, "status": 0},#terreo
    {"endereco": 0xA8, "status": 0},#1andar
    {"endereco": 0xA9, "status": 0},#2andar
    {"endereco": 0xAA, "status": 0}#3andar
]
listaEscreveRegE1 = [0,0,0,0,0,0,0,0,0,0,0]
listaEscreveRegE2 = [0,0,0,0,0,0,0,0,0,0,0]
fila_E1 = []
fila_E2 = []
escreveRegE1 = 0
escreveRegE2 = 0
temperaturaE1 = 0
temperaturaE2 = 0
andarAtual_E1 = 0
andarAtual_E2 = 0
pwmMotor1 = 0
pwmMotor2 = 0
encoder1 = 0
encoder2 = 0
stopThreads = 0
escalonador_UART = None

GPIO_DIR1_E1 = None
GPIO_DIR2_E1 = None 
GPIO_POTM_E1 = None 
GPIO_SENSOR_TERREO_E1 = None 
GPIO_SENSOR_1_ANDAR_E1 = None 
GPIO_SENSOR_2_ANDAR_E1 = None 
GPIO_SENSOR_3_ANDAR_E1 = None 


GPIO_DIR1_E2 = None
GPIO_DIR2_E2 = None 
GPIO_POTM_E2 = None 
GPIO_SENSOR_TERREO_E2 = None 
GPIO_SENSOR_1_ANDAR_E2 = None 
GPIO_SENSOR_2_ANDAR_E2 = None 
GPIO_SENSOR_3_ANDAR_E2 = None 

INTENSIDADE_MOTOR_E1 = 0
INTENSIDADE_MOTOR_E2 = 0

ESTADO_ELEVADOR_E1 = 0
ESTADO_ELEVADOR_E2 = 0

POS_TERREO_E1 = 0
POS_ANDAR1_E1 = 0
POS_ANDAR2_E1 = 0
POS_ANDAR3_E1 = 0
BSD_TERREO_E1 = [0,0]
BSD_ANDAR1_E1 = [0,0]
BSD_ANDAR2_E1 = [0,0]
BSD_ANDAR3_E1 = [0,0]

POS_TERREO_E2 = 0
POS_ANDAR1_E2 = 0
POS_ANDAR2_E2 = 0
POS_ANDAR3_E2 = 0
BSD_TERREO_E2 = [0,0]
BSD_ANDAR1_E2 = [0,0]
BSD_ANDAR2_E2 = [0,0]
BSD_ANDAR3_E2 = [0,0]






