import RPi.GPIO as GPIO
import time
import json
import sys
import variables
sys.path.append('..')

def define_GPIO(conf, elevador_num):
    variaveis = {
        'DIR1': None,
        'DIR2': None,
        'POTM': None,
        'SENSOR_TERREO': None,
        'SENSOR_1_ANDAR': None,
        'SENSOR_2_ANDAR': None,
        'SENSOR_3_ANDAR': None
    }

    for item in conf[f'elevador{elevador_num}']:
        name = item['name']
        gpio_pin = item['gpio']
        direction = item['direction']
        
        variaveis[name] = gpio_pin

        if direction == 'OUTPUT':
            GPIO.setup(gpio_pin, GPIO.OUT)
        elif direction == 'INPUT':
            GPIO.setup(gpio_pin, GPIO.IN, pull_up_down=GPIO.PUD_DOWN)
            #GPIO.add_event_detect(gpio_pin, GPIO.RISING)
        else:
            raise ValueError(f"Direção desconhecida: {direction}")
    
    if elevador_num == 1:
        variables.GPIO_DIR1_E1 = variaveis['DIR1']
        variables.GPIO_DIR2_E1 = variaveis['DIR2']
        variables.GPIO_POTM_E1 = variaveis['POTM']
        variables.GPIO_SENSOR_TERREO_E1 = variaveis['SENSOR_TERREO']
        variables.GPIO_SENSOR_1_ANDAR_E1 = variaveis['SENSOR_1_ANDAR']
        variables.GPIO_SENSOR_2_ANDAR_E1 = variaveis['SENSOR_2_ANDAR']
        variables.GPIO_SENSOR_3_ANDAR_E1 = variaveis['SENSOR_3_ANDAR']
    elif elevador_num == 2:
        variables.GPIO_DIR1_E2 = variaveis['DIR1']
        variables.GPIO_DIR2_E2 = variaveis['DIR2']
        variables.GPIO_POTM_E2 = variaveis['POTM']
        variables.GPIO_SENSOR_TERREO_E2 = variaveis['SENSOR_TERREO']
        variables.GPIO_SENSOR_1_ANDAR_E2 = variaveis['SENSOR_1_ANDAR']
        variables.GPIO_SENSOR_2_ANDAR_E2 = variaveis['SENSOR_2_ANDAR']
        variables.GPIO_SENSOR_3_ANDAR_E2 = variaveis['SENSOR_3_ANDAR']

def load_json(arq):
    with open(arq, 'r') as arqJson:
        configPins = json.load(arqJson)
    return configPins

def printar_status_var():
    vars_dict = {name: value for name, value in vars(variables).items() if name.startswith('GPIO_')}
    for name, value in vars_dict.items():
        print(f'variables.{name} = {value}')

def configura_GPIO():
    config = load_json(variables.arquivo_config_gpio)
    #GPIO.cleanup() 
    GPIO.setwarnings(False)
    GPIO.setmode(GPIO.BCM)  
    define_GPIO(config, 1)
    variables.INTENSIDADE_MOTOR_E1 = GPIO.PWM(variables.GPIO_POTM_E1, 100)
    variables.INTENSIDADE_MOTOR_E1.start(0)
    variables.INTENSIDADE_MOTOR_E1.ChangeDutyCycle(0)
    define_GPIO(config, 2)
    variables.INTENSIDADE_MOTOR_E2 = GPIO.PWM(variables.GPIO_POTM_E2, 100)
    variables.INTENSIDADE_MOTOR_E2.start(0)
    variables.INTENSIDADE_MOTOR_E2.ChangeDutyCycle(0)

def elevador_libera(elevador):
    if elevador == 1:
        GPIO.output(variables.GPIO_DIR1_E1, GPIO.LOW)
        GPIO.output(variables.GPIO_DIR2_E1, GPIO.LOW)
        variables.ESTADO_ELEVADOR_E1 = 0
        #print("Elevador 1 liberado")
    elif elevador == 2:
        GPIO.output(variables.GPIO_DIR1_E2, GPIO.LOW)
        GPIO.output(variables.GPIO_DIR2_E2, GPIO.LOW)
        variables.ESTADO_ELEVADOR_E2 = 0
        #print("Elevador 2 liberado")

def elevador_sobe(elevador):
    if elevador == 1:
        GPIO.output(variables.GPIO_DIR1_E1, GPIO.HIGH)
        GPIO.output(variables.GPIO_DIR2_E1, GPIO.LOW)
        variables.ESTADO_ELEVADOR_E1 = 1
        #print("Elevador 1 subindo")
    elif elevador == 2:
        GPIO.output(variables.GPIO_DIR1_E2, GPIO.HIGH)
        GPIO.output(variables.GPIO_DIR2_E2, GPIO.LOW)
        variables.ESTADO_ELEVADOR_E2 = 1
        #print("Elevador 2 subindo")

def elevador_desce(elevador):
    if elevador == 1:
        GPIO.output(variables.GPIO_DIR1_E1, GPIO.LOW)
        GPIO.output(variables.GPIO_DIR2_E1, GPIO.HIGH)
        variables.ESTADO_ELEVADOR_E1 = 2
        #print("Elevador 1 descendo")
    elif elevador == 2:
        GPIO.output(variables.GPIO_DIR1_E2, GPIO.LOW)
        GPIO.output(variables.GPIO_DIR2_E2, GPIO.HIGH)
        variables.ESTADO_ELEVADOR_E2 = 2
        #print("Elevador 2 descendo")

def elevador_freia(elevador):
    GPIO.setmode(GPIO.BCM)  
    if elevador == 1:
        GPIO.output(variables.GPIO_DIR1_E1, GPIO.HIGH)
        GPIO.output(variables.GPIO_DIR2_E1, GPIO.HIGH)
        variables.pwmMotor1 = 0
        variables.ESTADO_ELEVADOR_E1 = 3
        #print("Elevador 1 freando")
    elif elevador == 2:
        GPIO.output(variables.GPIO_DIR1_E2, GPIO.HIGH)
        GPIO.output(variables.GPIO_DIR2_E2, GPIO.HIGH)
        variables.pwmMotor2 = 0
        variables.ESTADO_ELEVADOR_E2 = 3
        #print("Elevador 2 freando")
def encerra_gpio():
    elevador_libera(1)
    elevador_libera(2)
    print("PWM dos motores em zero!")

    variables.INTENSIDADE_MOTOR_E1.ChangeDutyCycle(0)
    variables.INTENSIDADE_MOTOR_E2.ChangeDutyCycle(0)
    variables.INTENSIDADE_MOTOR_E1.stop()
    variables.INTENSIDADE_MOTOR_E2.stop()
    print("Motores parados")
    GPIO.cleanup()
    print("GPIO limpa e encerrada!")