import sys
import os
import threading
import signal
import time
from datetime import datetime
import RPi.GPIO as GPIO
import pickle

sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), 'modules')))
import variables
import uart
import i2c
import gpio
import pid
import salvaCalibragem
import oled


counter = 0

botoes_event = threading.Event()
envia_pwm_event = threading.Event()
encoders_event = threading.Event()
temperatura_event = threading.Event()
oled_event = threading.Event()

def is_in_queue(q, item):
    return item in list(q.queue)

def configuraDependencias():
    oled.tentaIniciarOLED()
        
    try:
        variables.escalonador_UART = uart.ESCALONADOR_UART(uart.DEVICE)
        variables.escalonador_UART.iniciaProcessamento()
        i2c.configuraI2c()
    except OSError as e:
        print(f"Erro ao iniciar {e}")

def thread_botoes():
    while variables.stopThreads == 0:
       botoes_event.wait()
       botoes_event.clear()
       btnE1 = uart.leBotoes(1,variables.matricula)
       if(btnE1):
        for i, status in enumerate(btnE1):
                if i < len(variables.listaBotoesE1):
                    variables.listaBotoesE1[i]["status"] = status
        btnE2 = uart.leBotoes(2,variables.matricula)
        if(btnE2):
            for i, status in enumerate(btnE2):
                    if i < len(variables.listaBotoesE2):
                        variables.listaBotoesE2[i]["status"] = status
        processaBotoes()

def thread_envia_pwm():
    
    while variables.stopThreads == 0:
        envia_pwm_event.wait()
        envia_pwm_event.clear()
        if(variables.pwmMotor1):
            uart.enviaPWM(1, abs(int(variables.pwmMotor1)), variables.matricula)
        if(variables.pwmMotor2):
            uart.enviaPWM(2, abs(int(variables.pwmMotor2)), variables.matricula)

def thread_encoders():
    while variables.stopThreads == 0:
        encoders_event.wait()
        encoders_event.clear()
        
        try:
            variables.encoder1 = uart.leEncoder(1, variables.matricula)
        except Exception as e:
            variables.encoder1 = -1
            print(f"Erro ao ler o encoder 1: {e}")

        try:
            variables.encoder2 = uart.leEncoder(2, variables.matricula)
        except Exception as e:
            variables.encoder2 = -1
            print(f"Erro ao ler o encoder 2: {e}")

def thread_oled():
    while variables.stopThreads == 0 and  variables.useOled == True:
        oled_event.wait() 
        oled_event.clear()  

        elevator1 = {'direction': variables.ESTADO_ELEVADOR_E1,
                     'floor': variables.andarAtual_E1,
                     'temperature': variables.temperaturaE1}
        elevator2 = {'direction': variables.ESTADO_ELEVADOR_E2,
                     'floor': variables.andarAtual_E2,
                     'temperature': variables.temperaturaE2}

        try:
            oled.update_display(elevator1, elevator2)
        except Exception as e:
            print(f"Erro ao atualizar o display: {e}")
            

def thread_temperatura():
    while variables.stopThreads == 0:
        temperatura_event.wait()
        temperatura_event.clear()
        
        variables.temperaturaE1 = i2c.leTemperaturaSensor(1)
        variables.temperaturaE2 = i2c.leTemperaturaSensor(2)
        
        if isinstance(variables.temperaturaE1, (int, float)):
            uart.enviaTemperatura(1, variables.temperaturaE1, variables.matricula)
        else:
            print(f"Temperatura E1 inválida: {variables.temperaturaE1}")
        
        if isinstance(variables.temperaturaE2, (int, float)):
            uart.enviaTemperatura(2, variables.temperaturaE2, variables.matricula)
        else:
            print(f"Temperatura E2 inválida: {variables.temperaturaE2}")

def iniciaThreadsComunicacoes():
    signal.signal(signal.SIGALRM, alarm_handler)
    signal.setitimer(signal.ITIMER_REAL, 0.01, 0.01)
    global botoes_thread,envia_pwm_thread,encoders_thread, temperatura_thread,oled_thread
    botoes_thread = threading.Thread(target=thread_botoes)
    envia_pwm_thread = threading.Thread(target=thread_envia_pwm)
    encoders_thread = threading.Thread(target=thread_encoders)
    temperatura_thread = threading.Thread(target=thread_temperatura)
    oled_thread = threading.Thread(target=thread_oled)
    oled_thread.start()
    botoes_thread.start()
    envia_pwm_thread.start()
    encoders_thread.start()
    temperatura_thread.start()

def alarm_handler(signum, frame):
    global counter
    counter += 1
    
    # Sinalizar threads com base no contador
    if counter % 5 == 0:  # 50ms (5 * 10ms)
        botoes_event.set()
    if counter % 5 == 0:  # 50ms (5 * 10ms)
        envia_pwm_event.set()
    if counter % 5 == 0:  # 200ms (20 * 10ms)
        encoders_event.set()
    if counter % 10 == 0:  # 10ms (10 * 10ms)
        temperatura_event.set()
    if counter % 10 == 0:  # 10ms (10 * 10ms)
        oled_event.set()

def signal_handler(sig, frame):
    variables.stopThreads = 1
    if sig == signal.SIGINT:
        print("Recebido SIGINT")
    elif sig == signal.SIGTERM:
        print("Recebido SIGTERM")
    try:
        if botoes_thread.is_alive():
            botoes_thread.join()
    except NameError:
        pass  

    try:
        if envia_pwm_thread.is_alive():
            envia_pwm_thread.join()
    except NameError:
        pass  

    try:
        if encoders_thread.is_alive():
            encoders_thread.join()
    except NameError:
        pass  

    try:
        if temperatura_thread.is_alive():
            temperatura_thread.join()
    except NameError:
        pass  

    try:
        if oled_thread.is_alive():
            oled_thread.join()
    except NameError:
        pass  
    
    if variables.useOled == True:
        oled.end_display()
    variables.escalonador_UART.fechaUART()
    gpio.encerra_gpio()
    i2c.fechaBus()
    # Sair do programa
    sys.exit(0)

# Função para calibrar o elevador 1
def calibra_elevador_1():
    pos_borda_subida = {}
    pos_borda_descida = {}
    
    def edge_detected(channel):
        sensor = None
        if channel == variables.GPIO_SENSOR_TERREO_E1:
            sensor = 'Térreo E1'
        elif channel == variables.GPIO_SENSOR_1_ANDAR_E1:
            sensor = 'Andar 1 E1'
        elif channel == variables.GPIO_SENSOR_2_ANDAR_E1:
            sensor = 'Andar 2 E1'
        elif channel == variables.GPIO_SENSOR_3_ANDAR_E1:
            sensor = 'Andar 3 E1'
        
        if sensor:
            if GPIO.input(channel) == GPIO.HIGH:  # Borda de subida
                pos_borda_subida[sensor] = variables.encoder1
                print(f"Encoder na borda de subida {sensor}: {variables.encoder1}")
            elif GPIO.input(channel) == GPIO.LOW:  # Borda de descida
                pos_borda_descida[sensor] = variables.encoder1
                print(f"Encoder na borda de descida {sensor}: {variables.encoder1}")

    # Configurar eventos de borda para sensores
    sensores = [
        variables.GPIO_SENSOR_TERREO_E1,
        variables.GPIO_SENSOR_1_ANDAR_E1,
        variables.GPIO_SENSOR_2_ANDAR_E1,
        variables.GPIO_SENSOR_3_ANDAR_E1
    ]
    
    for sensor in sensores:
        GPIO.add_event_detect(sensor, GPIO.BOTH, callback=edge_detected)

    # Mover o elevador para registrar as bordas
    gpio.elevador_sobe(1)
    variables.pwmMotor1 = 5
    variables.INTENSIDADE_MOTOR_E1.ChangeDutyCycle(variables.pwmMotor1)

    # Esperar até que todas as bordas sejam detectadas
    while True:
        todos_detectados = all(sensor in pos_borda_subida and sensor in pos_borda_descida for sensor in ['Térreo E1', 'Andar 1 E1', 'Andar 2 E1', 'Andar 3 E1'])
        if todos_detectados or variables.stopThreads != 0:
            gpio.elevador_freia(1)
            variables.pwmMotor1 = 0
            variables.INTENSIDADE_MOTOR_E1.ChangeDutyCycle(variables.pwmMotor1)
            break
        time.sleep(0.001)

    # Desabilitar eventos de borda
    for sensor in sensores:
        GPIO.remove_event_detect(sensor)

    # Calcular e imprimir a posição central para cada sensor
    for sensor in ['Térreo E1', 'Andar 1 E1', 'Andar 2 E1', 'Andar 3 E1']:
        if sensor in pos_borda_subida and sensor in pos_borda_descida:
            pos_central = calcular_pos_central(pos_borda_subida[sensor], pos_borda_descida[sensor])
            bs = pos_borda_subida[sensor]
            bd = pos_borda_descida[sensor]
            if sensor == 'Térreo E1':
                variables.POS_TERREO_E1 = pos_central
                variables.BSD_TERREO_E1 = [bs,bd]
            elif sensor == 'Andar 1 E1':
                variables.POS_ANDAR1_E1 = pos_central
                variables.BSD_ANDAR1_E1 = [bs,bd]
            elif sensor == 'Andar 2 E1':
                variables.POS_ANDAR2_E1 = pos_central
                variables.BSD_ANDAR2_E1 = [bs,bd]
            elif sensor == 'Andar 3 E1':
                variables.POS_ANDAR3_E1 = pos_central
                variables.BSD_ANDAR3_E1 = [bs,bd]
            print(f"Posição central {sensor}: {pos_central}")

# Função para calibrar o elevador 2
def calibra_elevador_2():
    pos_borda_subida = {}
    pos_borda_descida = {}
    
    def edge_detected(channel):
        sensor = None
        if channel == variables.GPIO_SENSOR_TERREO_E2:
            sensor = 'Térreo E2'
        elif channel == variables.GPIO_SENSOR_1_ANDAR_E2:
            sensor = 'Andar 1 E2'
        elif channel == variables.GPIO_SENSOR_2_ANDAR_E2:
            sensor = 'Andar 2 E2'
        elif channel == variables.GPIO_SENSOR_3_ANDAR_E2:
            sensor = 'Andar 3 E2'
        
        if sensor:
            if GPIO.input(channel) == GPIO.HIGH:  # Borda de subida
                pos_borda_subida[sensor] = variables.encoder2
                print(f"Encoder na borda de subida {sensor}: {variables.encoder2}")
            elif GPIO.input(channel) == GPIO.LOW:  # Borda de descida
                pos_borda_descida[sensor] = variables.encoder2
                print(f"Encoder na borda de descida {sensor}: {variables.encoder2}")

    # Configurar eventos de borda para sensores
    sensores = [
        variables.GPIO_SENSOR_TERREO_E2,
        variables.GPIO_SENSOR_1_ANDAR_E2,
        variables.GPIO_SENSOR_2_ANDAR_E2,
        variables.GPIO_SENSOR_3_ANDAR_E2
    ]
    
    for sensor in sensores:
        GPIO.add_event_detect(sensor, GPIO.BOTH, callback=edge_detected)

    # Mover o elevador para registrar as bordas
    gpio.elevador_sobe(2)
    variables.pwmMotor2 = 5
    variables.INTENSIDADE_MOTOR_E2.ChangeDutyCycle(variables.pwmMotor2)

    # Esperar até que todas as bordas sejam detectadas
    while True:
        todos_detectados = all(sensor in pos_borda_subida and sensor in pos_borda_descida for sensor in ['Térreo E2', 'Andar 1 E2', 'Andar 2 E2', 'Andar 3 E2'])
        if todos_detectados or variables.stopThreads != 0:
            gpio.elevador_freia(2)
            variables.pwmMotor2 = 0
            variables.INTENSIDADE_MOTOR_E2.ChangeDutyCycle(variables.pwmMotor2)
            break
        time.sleep(0.001)

    # Desabilitar eventos de borda
    for sensor in sensores:
        GPIO.remove_event_detect(sensor)

    # Calcular e imprimir a posição central para cada sensor
    for sensor in ['Térreo E2', 'Andar 1 E2', 'Andar 2 E2', 'Andar 3 E2']:
        if sensor in pos_borda_subida and sensor in pos_borda_descida:
            pos_central = calcular_pos_central(pos_borda_subida[sensor], pos_borda_descida[sensor])
            bs = pos_borda_subida[sensor]
            bd = pos_borda_descida[sensor]
            if sensor == 'Térreo E2':
                variables.POS_TERREO_E2 = pos_central
                variables.BSD_TERREO_E2 = [bs,bd]
            elif sensor == 'Andar 1 E2':
                variables.POS_ANDAR1_E2 = pos_central
                variables.BSD_ANDAR1_E2 = [bs,bd]
            elif sensor == 'Andar 2 E2':
                variables.POS_ANDAR2_E2 = pos_central
                variables.BSD_ANDAR2_E2 = [bs,bd]
            elif sensor == 'Andar 3 E2':
                variables.POS_ANDAR3_E2 = pos_central
                variables.BSD_ANDAR3_E2 = [bs,bd]
            print(f"Posição central {sensor}: {pos_central}")

# Função auxiliar para calcular a posição central
def calcular_pos_central(pos_subida, pos_descida):
    if pos_subida is not None and pos_descida is not None:
        return (pos_subida + pos_descida) / 2
    return None

def tentaReestabelecerUART(encoder_num):
    for tentativa in range(5):
        print(f"Estou com problemas para ler o encoder {encoder_num}, tentando reestabelecer a UART ({tentativa + 1}/5)...")
        time.sleep(5)
        try:
            if encoder_num == 1:
                variables.encoder1 = uart.leEncoder(1, variables.matricula)
            elif encoder_num == 2:
                variables.encoder2 = uart.leEncoder(2, variables.matricula)
            
            if (encoder_num == 1 and variables.encoder1 != -1) or (encoder_num == 2 and variables.encoder2 != -1):
                return True
        except Exception as e:
            print(f"Erro ao tentar reestabelecer a UART: {e}")
    
    return False

def iniciaCalibragem():
    print("Aguarde... Calibrando elevadores")
    time.sleep(2)
    print(f"ENCODER ELEVADOR 1: {variables.encoder1}")
    print(f"ENCODER ELEVADOR 2: {variables.encoder2}")

    if variables.encoder1 == -1:
        if not tentaReestabelecerUART(1):
            print("Estou com erro na UART. Verifique se a UART dessa placa está funcionando ou tente em outra placa!")
            return -1

    if variables.encoder2 == -1:
        if not tentaReestabelecerUART(2):
            print("Estou com erro na UART. Verifique se a UART dessa placa está funcionando ou tente em outra placa!")
            return -1

    if variables.encoder1 > 0:
        print("OPS! O ENCODER 1 ESTÁ FORA DA POSIÇÃO IDEAL, AJUSTANDO...")
        gpio.elevador_sobe(1)
        time.sleep(0.5)
        gpio.elevador_desce(1)
        variables.pwmMotor1 = 100
        variables.INTENSIDADE_MOTOR_E1.ChangeDutyCycle(variables.pwmMotor1)
        while variables.encoder1 > 0:
            time.sleep(0.001)
        gpio.elevador_freia(1)
        variables.pwmMotor1 = 0
        variables.INTENSIDADE_MOTOR_E1.ChangeDutyCycle(variables.pwmMotor1)

    if variables.encoder2 > 0:
        print("OPS! O ENCODER 2 ESTÁ FORA DA POSIÇÃO IDEAL, AJUSTANDO...")
        gpio.elevador_sobe(2)
        time.sleep(1)
        gpio.elevador_desce(2)
        variables.pwmMotor2 = 100
        variables.INTENSIDADE_MOTOR_E2.ChangeDutyCycle(variables.pwmMotor2)
        while variables.encoder2 > 0:
            time.sleep(0.001)
        gpio.elevador_freia(2)
        variables.pwmMotor2 = 0
        variables.INTENSIDADE_MOTOR_E2.ChangeDutyCycle(variables.pwmMotor2)

    time.sleep(2)
    print("OK, INICIANDO CALIBRAGEM...")
    thread_elevador1 = threading.Thread(target=calibra_elevador_1, args=())
    thread_elevador2 = threading.Thread(target=calibra_elevador_2, args=())
    thread_elevador1.start()
    thread_elevador2.start()
    thread_elevador1.join()
    thread_elevador2.join()
    print("Calibração dos elevadores concluída.")
    return True

def toAndar(elevador, andar):
    if elevador == 1:
        encoder = variables.encoder1
        pos_andar = [variables.POS_TERREO_E1, variables.POS_ANDAR1_E1, variables.POS_ANDAR2_E1, variables.POS_ANDAR3_E1]
        bsd_andar = [variables.BSD_TERREO_E1, variables.BSD_ANDAR1_E1, variables.BSD_ANDAR2_E1, variables.BSD_ANDAR3_E1]
        pwm_motor = variables.INTENSIDADE_MOTOR_E1
        gpio_sensor = [variables.GPIO_SENSOR_TERREO_E1, variables.GPIO_SENSOR_1_ANDAR_E1, variables.GPIO_SENSOR_2_ANDAR_E1, variables.GPIO_SENSOR_3_ANDAR_E1]
        variables.deslocamento_E1[0] = variables.encoder1
        
    elif elevador == 2:
        encoder = variables.encoder2
        pos_andar = [variables.POS_TERREO_E2, variables.POS_ANDAR1_E2, variables.POS_ANDAR2_E2, variables.POS_ANDAR3_E2]
        bsd_andar = [variables.BSD_TERREO_E2, variables.BSD_ANDAR1_E2, variables.BSD_ANDAR2_E2, variables.BSD_ANDAR3_E2]
        pwm_motor = variables.INTENSIDADE_MOTOR_E2
        gpio_sensor = [variables.GPIO_SENSOR_TERREO_E2, variables.GPIO_SENSOR_1_ANDAR_E2, variables.GPIO_SENSOR_2_ANDAR_E2, variables.GPIO_SENSOR_3_ANDAR_E2]
        variables.deslocamento_E2[0] = variables.encoder2
    else:
        raise ValueError("Elevador inválido")

    if andar < 0 or andar > 3:
        raise ValueError("Andar inválido. Deve ser 0 (terreo), 1, 2 ou 3.")

    target_position = pos_andar[andar]
    delay_before_stop = 500  # Unidades de encoder antes da posição desejada para começar a frear

    # Configuração do PID
    #professor Kp=0.005, Ki=0.0, Kd=0.01, T=1.0
    pid_controller = pid.PIDController(
        Kp=0.01, Ki=0.01, Kd=0.05, T=1.0, 
    sinal_de_controle_MAX=100.0, sinal_de_controle_MIN=-100.0
    )
    count_desloc = 0
    while True and variables.stopThreads == 0:
        if(elevador == 1):
            saida_medida = variables.encoder1
        else:
            saida_medida = variables.encoder2

        ref = target_position
        pid_controller.atualiza_referencia(target_position)  # 
    

        pwm_value = pid_controller.calcula_sinal_de_controle(saida_medida)
        
        if pwm_value >= 0 :
            gpio.elevador_sobe(elevador)
        else:
            gpio.elevador_desce(elevador)
        pwm_motor.ChangeDutyCycle(abs(pwm_value))

        #print(f"Referencia {ref} atual {saida_medida} pwm {pwm_value}")

        if(elevador == 1):
            variables.pwmMotor1 = pwm_value
        else:
            variables.pwmMotor2 = pwm_value

        # Movimentação do elevador
        if saida_medida < target_position:
            if elevador == 1:
                gpio.elevador_sobe(1)
            elif elevador == 2:
                gpio.elevador_sobe(2)
        elif saida_medida > target_position:
            if elevador == 1:
                gpio.elevador_desce(1)
            elif elevador == 2:
                gpio.elevador_desce(2)

        if elevador == 1 and variables.emergencia_E1:
            gpio.elevador_freia(elevador)
            pwm_motor.ChangeDutyCycle(0)
            break
        if elevador == 2 and variables.emergencia_E2:
            gpio.elevador_freia(elevador)
            pwm_motor.ChangeDutyCycle(0)
            break



        
        if saida_medida >= bsd_andar[andar][0] and saida_medida <= bsd_andar[andar][1]  and andar == 0 and GPIO.input(gpio_sensor[0]) == GPIO.HIGH:
            print("parado pelo encoder no terreo")
            gpio.elevador_freia(elevador)
            pwm_motor.ChangeDutyCycle(0)
            if elevador == 1:
                variables.andarAtual_E1 = "T"
            else:
                variables.andarAtual_E2 = "T"
            break
        elif saida_medida >= bsd_andar[andar][0] and saida_medida <= bsd_andar[andar][1]  and andar == 1 and GPIO.input(gpio_sensor[1]) == GPIO.HIGH:
            print("parado pelo encoder no andar 1")
            gpio.elevador_freia(elevador)
            pwm_motor.ChangeDutyCycle(0)
            if elevador == 1:
                variables.andarAtual_E1 = "1"
            else:
                variables.andarAtual_E2 = "1"
            break
        elif saida_medida >= bsd_andar[andar][0] and saida_medida <= bsd_andar[andar][1]  and andar == 2  and GPIO.input(gpio_sensor[2]) == GPIO.HIGH:
            print("parado pelo encoder no andar 2")
            gpio.elevador_freia(elevador)
            pwm_motor.ChangeDutyCycle(0)
            if elevador == 1:
                variables.andarAtual_E1 = "2"
            else:
                variables.andarAtual_E2 = "2"
            break
        elif saida_medida >= bsd_andar[andar][0] and saida_medida <= bsd_andar[andar][1]  and andar == 3  and GPIO.input(gpio_sensor[3]) == GPIO.HIGH:
            print("parado pelo encoder no andar 3")
            gpio.elevador_freia(elevador)
            pwm_motor.ChangeDutyCycle(0)
            if elevador == 1:
                variables.andarAtual_E1 = "3"
            else:
                variables.andarAtual_E2 = "3"
            break
        
        # Verificação do sensor
        if(elevador == 1):
            variables.deslocamento_E1[1] = saida_medida
            if variables.deslocamento_E1[0] == variables.deslocamento_E1[1] and count_desloc >=10 and count_desloc<=15:
                print("OPS! Verifiquei que o elevador 1 nao saiu do lugar... tentando resolver")
                gpio.elevador_desce(1)
                time.sleep(0.5)
                gpio.elevador_sobe(1)
                time.sleep(0.5)
                gpio.elevador_desce(1)
                time.sleep(0.5)
                gpio.elevador_sobe(1)
                time.sleep(0.5)
                variables.verificadoErro_E1= 1
            elif variables.deslocamento_E1[0] == variables.deslocamento_E1[1] and count_desloc >=16 and count_desloc<=40:
                print("OPS! Verifiquei que o elevador 1 nao saiu do lugar... tentando resolver")
                gpio.elevador_desce(1)
                variables.INTENSIDADE_MOTOR_E1.stop()
                variables.INTENSIDADE_MOTOR_E1.start(0)
                variables.INTENSIDADE_MOTOR_E1.ChangeDutyCycle(100)
                time.sleep(0.5)
                gpio.elevador_sobe(1)
                time.sleep(0.5)
                gpio.elevador_desce(1)
                time.sleep(0.5)
                gpio.elevador_sobe(1)
                time.sleep(0.5)
            elif variables.deslocamento_E1[0] == variables.deslocamento_E1[1]  and count_desloc>=41:
                print("Verifiquei que o elevador 1 continua travado, reinicie o dashboard e rode o programa novamente!")
                
        else:
            variables.deslocamento_E2[1] = saida_medida
            if variables.deslocamento_E2[0] == variables.deslocamento_E2[1] and count_desloc >=10 and count_desloc<=15:
                gpio.elevador_desce(2)
                time.sleep(0.5)
                gpio.elevador_sobe(2)
                time.sleep(0.5)
                gpio.elevador_desce(2)
                time.sleep(0.5)
                gpio.elevador_sobe(2)
                time.sleep(0.5)
                variables.verificadoErro_E1= 1
            elif variables.deslocamento_E2[0] == variables.deslocamento_E2[1] and count_desloc >=16 and count_desloc<=40:
                print("OPS! Verifiquei que o elevador 1 nao saiu do lugar... tentando resolver")
                gpio.elevador_desce(2)
                variables.INTENSIDADE_MOTOR_E2.stop()
                variables.INTENSIDADE_MOTOR_E2.start(0)
                variables.INTENSIDADE_MOTOR_E2.ChangeDutyCycle(100)
                time.sleep(0.5)
                gpio.elevador_sobe(2)
                time.sleep(0.5)
                gpio.elevador_desce(2)
                time.sleep(0.5)
                gpio.elevador_sobe(2)
                time.sleep(0.5)
            elif variables.deslocamento_E2[0] == variables.deslocamento_E2[1]  and count_desloc>=41:
                print("Verifiquei que o elevador 2 continua travado, reinicie o dashboard e rode o programa novamente!")
            else:
                if elevador == 1 and variables.verificadoErro_E1 == 1:
                    print("Erro aparentemente resolvido no elevador 1, se persistir reinicie o dash e o programa")
                    variables.verificadoErro_E1 = 0
                elif elevador == 2 and variables.verificadoErro_E2 == 1:
                    print("Erro aparentemente resolvido no elevador 2, se persistir reinicie o dash e o programa")
                    variables.verificadoErro_E2 = 0

        count_desloc+=1
        time.sleep(1)

    gpio.elevador_freia(elevador)
    #print(f"Elevador {elevador} freiou em {saida_medida}, deveria ter freado em {target_position}")

def escolheElevador(andar):
    # Verifica a posição do andar solicitado para cada elevador
    if andar == 0:
        posicao_andares = [variables.POS_TERREO_E1, variables.POS_TERREO_E2]
    elif andar == 1:
        posicao_andares = [variables.POS_ANDAR1_E1, variables.POS_ANDAR1_E2]
    elif andar == 2:
        posicao_andares = [variables.POS_ANDAR2_E1, variables.POS_ANDAR2_E2]
    elif andar == 3:
        posicao_andares = [variables.POS_ANDAR3_E1, variables.POS_ANDAR3_E2]
    else:
        raise ValueError("Andar inválido. Deve ser 0, 1, 2 ou 3.")
    
    # Calcula a distância dos elevadores para o andar solicitado
    dist_e1 = abs(variables.encoder1 - posicao_andares[0])
    dist_e2 = abs(variables.encoder2 - posicao_andares[1])

    # Escolhe o elevador mais próximo
    elevador = 1 if dist_e1 < dist_e2 else 2

    return elevador


def atendeSolicitacao(andar):
    elevador = escolheElevador(andar)
    toAndar(elevador, andar)
    
def verificaCalibragem():
    hostname = salvaCalibragem.get_hostname()
    filename = f'calibragem_{hostname}.calibration'

    if os.path.exists(filename):
        usar_existente = input(f"Arquivo '{filename}' encontrado. Deseja usar a calibragem existente? (s/n): ").strip().lower()
        if usar_existente == 's':
            if salvaCalibragem.carregar_calibragem(filename):
                print("Calibragem carregada com sucesso.")
            else:
                print("Falha ao carregar a calibragem. Realizando nova calibragem...")
                if not iniciaCalibragem() == -1:
                    salvaCalibragem.salvar_calibragem(filename)
                    print(f"Nova calibragem salva em '{filename}'.")
        else:
            print("Realizando nova calibragem...")
            if not iniciaCalibragem() == -1:
                salvaCalibragem.salvar_calibragem(filename)
                print(f"Nova calibragem salva em '{filename}'.")
    else:
        print("Arquivo de calibragem não encontrado. Calibrando...")
        if not iniciaCalibragem() == -1:
                salvaCalibragem.salvar_calibragem(filename)
                print(f"Nova calibragem salva em '{filename}'.")

def processar_botoes(lista_botoes, elevador, fila):
    # Mapeamento dos botões para ações
    botoes_elevador1 = {
        0x06: 'emergencia',
        0x00: 0,  # Terreo
        0x01: 1,  # 1andar
        0x02: 1,  # 1andar
        0x03: 2,  # 2andar
        0x04: 2,  # 2andar
        0x05: 3,  # 3andar
        0x07: 0,  # Terreo
        0x08: 1,  # 1andar
        0x09: 2,  # 2andar
        0x0A: 3   # 3andar
    }
    
    botoes_elevador2 = {
        0xA6: 'emergencia',
        0xA0: 0,  # Terreo
        0xA7: 0,  # Terreo
        0xA1: 1,  # 1andar
        0xA2: 1,  # 1andar
        0xA8: 1,  # 1andar
        0xA3: 2,  # 2andar
        0xA4: 2,  # 2andar
        0xA9: 2,  # 2andar
        0xA5: 3,  # 3andar
        0xAA: 3   # 3andar
    }
    
    if elevador == 1:
        botoes = botoes_elevador1
    elif elevador == 2:
        botoes = botoes_elevador2
    else:
        raise ValueError("Elevador inválido. Use 1 ou 2.")
    
    # Coleta os botões acionados
    botoes_acionados = {botao["endereco"] for botao in lista_botoes if botao["status"] == 1}
    
    #print(f"Botoes acionados para elevador {elevador}: {botoes_acionados}")
    
    # Processa os botões acionados e adiciona à fila
    for botao in botoes_acionados:
        if botao in botoes:
            acao = botoes[botao]
            if acao == 'emergencia':
                if elevador == 1:
                    variables.emergencia_E1 = 1
                else:
                    variables.emergencia_E2 = 1

            else:
                # Adiciona à fila apenas se o valor não estiver em qualquer posição da fila
                if acao not in fila:
                    fila.append(acao)
                    #print(f"Acionou fila {fila} com valor {acao} para elevador {elevador}")
        else:
            ...
            #print(f"Botão {botao} não está mapeado para elevador {elevador}")

fila_E1= []
fila_E2= []

def controleElevador1():
    global fila_E1
    while variables.stopThreads == 0:
        time.sleep(1)
        #print(fila_E1)
        if(len(fila_E1)>0):
            movePos = fila_E1[0]
            toAndar(1,movePos)
            if(variables.emergencia_E1):
                fila_E1 = []
                uart.escreveBotoes(1, 0x00,0,  variables.matricula)
                uart.escreveBotoes(1, 0x07,0, variables.matricula)
                uart.escreveBotoes(1, 0x01, 0,  variables.matricula)
                uart.escreveBotoes(1, 0x02, 0, variables.matricula)
                uart.escreveBotoes(1, 0x08, 0, variables.matricula)
                uart.escreveBotoes(1, 0x03, 0,  variables.matricula)
                uart.escreveBotoes(1, 0x04, 0, variables.matricula)
                uart.escreveBotoes(1, 0x09, 0, variables.matricula)
                uart.escreveBotoes(1, 0x05, 0,  variables.matricula)
                uart.escreveBotoes(1, 0x0A, 0, variables.matricula)
                time.sleep(1)
                fila_E1 = []
                print("EMERGENCIA!!!! Elevador 1 parado, botoes apagados e fila zerada")
                time.sleep(1)
                uart.escreveBotoes(1, 0x06, 0, variables.matricula)
                variables.emergencia_E1 = 0
            else:
                if(movePos == 0):
                    uart.escreveBotoes(1, 0x00,0,  variables.matricula)
                    uart.escreveBotoes(1, 0x07,0, variables.matricula)
                elif(movePos == 1):
                    uart.escreveBotoes(1, 0x01, 0,  variables.matricula)
                    uart.escreveBotoes(1, 0x02, 0, variables.matricula)
                    uart.escreveBotoes(1, 0x08, 0, variables.matricula)
                elif(movePos == 2):
                    uart.escreveBotoes(1, 0x03, 0,  variables.matricula)
                    uart.escreveBotoes(1, 0x04, 0, variables.matricula)
                    uart.escreveBotoes(1, 0x09, 0, variables.matricula)
                elif(movePos == 3):
                    uart.escreveBotoes(1, 0x05, 0,  variables.matricula)
                    uart.escreveBotoes(1, 0x0A, 0, variables.matricula)
                time.sleep(0.5)
                fila_E1.pop(0)

def controleElevador2():
    global fila_E2
    while variables.stopThreads == 0:
        if len(fila_E2) > 0:
            movePos = fila_E2[0]
            toAndar(2, movePos)

            if(variables.emergencia_E2):
                fila_E2 = []
                uart.escreveBotoes(2, 0xA0,0,  variables.matricula)
                uart.escreveBotoes(2, 0xA7,0, variables.matricula)
                uart.escreveBotoes(2, 0xA1, 0,  variables.matricula)
                uart.escreveBotoes(2, 0xA2, 0, variables.matricula)
                uart.escreveBotoes(2, 0xA8, 0, variables.matricula)
                uart.escreveBotoes(2, 0xA3, 0,  variables.matricula)
                uart.escreveBotoes(2, 0xA4, 0, variables.matricula)
                uart.escreveBotoes(2, 0xA9, 0, variables.matricula)
                uart.escreveBotoes(2, 0xA5, 0,  variables.matricula)
                uart.escreveBotoes(2, 0xAA, 0, variables.matricula)
                time.sleep(1)
                fila_E2 = []
                print("EMERGENCIA!!!! Elevador 2 parado, botoes apagados e fila zerada")
                time.sleep(1)
                uart.escreveBotoes(1, 0xA6, 0, variables.matricula)
                variables.emergencia_E2 = 0
            else:
            
                if movePos == 0:
                    uart.escreveBotoes(2, 0xA0, 0, variables.matricula)
                    uart.escreveBotoes(2, 0xA7, 0, variables.matricula)
                elif movePos == 1:
                    uart.escreveBotoes(2, 0xA1, 0, variables.matricula)
                    uart.escreveBotoes(2, 0xA2, 0, variables.matricula)
                    uart.escreveBotoes(2, 0xA8, 0, variables.matricula)
                elif movePos == 2:
                    uart.escreveBotoes(2, 0xA3, 0, variables.matricula)
                    uart.escreveBotoes(2, 0xA4, 0, variables.matricula)
                    uart.escreveBotoes(2, 0xA9, 0, variables.matricula)
                elif movePos == 3:
                    uart.escreveBotoes(2, 0xA5, 0, variables.matricula)
                    uart.escreveBotoes(2, 0xAA, 0, variables.matricula)
                    
                time.sleep(0.5)
                fila_E2.pop(0)

def processaBotoes():
    global fila_E1, fila_E2
    listaBot1 = variables.listaBotoesE1
    processar_botoes(listaBot1, 1, fila_E1)
    listaBot2 = variables.listaBotoesE2
    processar_botoes(listaBot2, 2, fila_E2)



def main():
    configuraDependencias()
    time.sleep(2)
    iniciaThreadsComunicacoes()
    #printaVariaveis()
    gpio.configura_GPIO()
    time.sleep(1)
    verificaCalibragem()
    thread_elevador1 = threading.Thread(target=controleElevador1)
    thread_elevador2 = threading.Thread(target=controleElevador2)
    thread_elevador1.start()
    thread_elevador2.start()
    thread_elevador1.join()
    thread_elevador2.join()
 
        
    
    
if __name__ == '__main__':
    signal.signal(signal.SIGINT, signal_handler)
    signal.signal(signal.SIGTERM, signal_handler)
    main()
