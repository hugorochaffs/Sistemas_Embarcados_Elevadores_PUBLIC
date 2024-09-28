import termios
import os
import struct
import threading
import queue
import time
from crc import calcula_CRC
import json
import variables  # VARIÁVEIS GLOBAIS

# CONSTANTES:
BAUDRATE = termios.B115200
WORD = termios.CS8
DEVICE = "/dev/serial0"
PARITY = termios.IGNPAR

# ENDEREÇOS
DISPOSITIVOATUAL = 0x00
DISPOSITIVOREMOTO = 0x01
ELEVADOR_MOTOR_1 = 0x00
ELEVADOR_MOTOR_2 = 0x01
BOTAO_INICIAL_ELEVADOR_1 = 0x00
BOTAO_INICIAL_ELEVADOR_2 = 0xA0

class ESCALONADOR_UART:
    def __init__(self, device):
        self.device = device
        self.uart_filestream = None
        self.lock = threading.Lock()
        self.queue = queue.Queue()
        self.iniciaUART()

    def iniciaUART(self):
        try:
            self.uart_filestream = os.open(self.device, os.O_RDWR | os.O_NOCTTY | os.O_NDELAY)
            [iflag, oflag, cflag, lflag] = [0, 1, 2, 3]
            attrs = termios.tcgetattr(self.uart_filestream)
            attrs[cflag] = BAUDRATE | WORD | termios.CLOCAL | termios.CREAD
            attrs[iflag] = PARITY
            attrs[oflag] = 0
            attrs[lflag] = 0
            termios.tcflush(self.uart_filestream, termios.TCIFLUSH)
            termios.tcsetattr(self.uart_filestream, termios.TCSANOW, attrs)
        except OSError as e:
            print(f"Erro ao iniciar UART: {e}")

    def fechaUART(self):
        try:
            if self.uart_filestream:
                os.close(self.uart_filestream)
                self.uart_filestream = None
                print("UART Fechada")
        except OSError as e:
            print(f"Erro ao fechar UART: {e}")

    def modbus(self, req, tamanho_resposta):
        try:
            crc = calcula_CRC(req)
            crc_high = (crc >> 8) & 0xFF
            crc_low = crc & 0xFF
            request_with_crc = req + [crc_low, crc_high]
            termios.tcflush(self.uart_filestream, termios.TCIOFLUSH)
            os.write(self.uart_filestream, bytes(request_with_crc))
            time.sleep(0.05)
            response = os.read(self.uart_filestream, tamanho_resposta)
            return response
        except OSError as e:
            print(f"Erro na operação Modbus: {e}")
            return None

    def processaRequisicoes(self):
        while True:
            command, result_queue, response_size = self.queue.get()
            with self.lock:
                response = self.modbus(command, response_size)
                result_queue.put(response)
            self.queue.task_done()

    def enviaComando(self, command, response_size):
        result_queue = queue.Queue()
        self.queue.put((command, result_queue, response_size))
        return result_queue.get()

    def iniciaProcessamento(self):
        processing_thread = threading.Thread(target=self.processaRequisicoes, daemon=True)
        processing_thread.start()


def converteMatricula(matricula):
    matricula = list(str(matricula))
    matricula = [int(d) for d in matricula]
    return matricula

def verificaResposta(send, response):
    if(len(response)>2):
        if response[2] == 35 or response[2] == 22:
            if response[0] == DISPOSITIVOATUAL and response[1] == send[1] and response[2] == send[2]:
                crcR = calcula_CRC(response[:len(response)-2])
                crc_high = (crcR >> 8) & 0xFF
                crc_low = crcR & 0xFF
                if response[-2] == crc_low and response[-1] == crc_high:
                    return True
        else:
            if response[0] == DISPOSITIVOATUAL and response[1] == send[1]:
                
                crcR = calcula_CRC(response[:len(response)-2])
                crc_high = (crcR >> 8) & 0xFF
                crc_low = crcR & 0xFF
                if response[-2] == crc_low and response[-1] == crc_high:
                    return True

        return False
    return False

def leEncoder(motor, matricula):
    scheduler = variables.escalonador_UART
    code = ELEVADOR_MOTOR_1 if motor == 1 else ELEVADOR_MOTOR_2
    request = [DISPOSITIVOREMOTO, 0x23, 0xC1, code] + converteMatricula(matricula)
    #print(request)
    response = scheduler.enviaComando(request, 9)
    #print(list(response))
    if response:
        lista_bytes = list(response)
        if verificaResposta(request, lista_bytes):
            #print(f"Recebida a lista: {lista_bytes}")
            dados_byte_array = response[3:7]
            int_value = int.from_bytes(dados_byte_array, "little")
            #print(int_value)
            return(int_value)
    return -1

def enviaPWM(motor, valorPWM, matricula):
    scheduler = variables.escalonador_UART
    code = ELEVADOR_MOTOR_1 if motor == 1 else ELEVADOR_MOTOR_2
    int_bytes = struct.pack('I', valorPWM)
    request = [DISPOSITIVOREMOTO, 0x16, 0xC2, code] + list(int_bytes) + converteMatricula(matricula)
    response = scheduler.enviaComando(request, 9)
    if response:
        lista_bytes = list(response)
        if verificaResposta(request, lista_bytes):
            #print(f'Resposta: {lista_bytes}')
            #print(f"Sucesso ao enviar PWM")
            return True
    return False

def enviaTemperatura(elevador, valorTemp, matricula):
    scheduler = variables.escalonador_UART
    code = ELEVADOR_MOTOR_1 if elevador == 1 else ELEVADOR_MOTOR_2
    float_bytes = struct.pack('f', valorTemp)
    request = [DISPOSITIVOREMOTO, 0x16, 0xD1, code] + list(float_bytes) + converteMatricula(matricula)
    response = scheduler.enviaComando(request, 9)
    if response:
        lista_bytes = list(response)
        if verificaResposta(request, lista_bytes):
           #print(f'Resposta: {lista_bytes}')
            #print(f"Sucesso ao enviar Temperatura")
            return True
    return False

def leBotoes(elevador, matricula):
    scheduler = variables.escalonador_UART
    code = BOTAO_INICIAL_ELEVADOR_1 if elevador == 1 else BOTAO_INICIAL_ELEVADOR_2
    request = [DISPOSITIVOREMOTO, 0x03, code, 11] + converteMatricula(matricula)
    
    response = scheduler.enviaComando(request, 15)
    
    if response:
        lista_bytes = list(response)
        if verificaResposta(request, lista_bytes):
            #print(f"Recebida a lista: {lista_bytes}")
            dados_byte_array = list(response[2:13])
            
            
            return dados_byte_array
    #return [0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0]

def escreveBotoes(elevador, botao, dado, matricula):
    scheduler = variables.escalonador_UART
    code = BOTAO_INICIAL_ELEVADOR_1 if elevador == 1 else BOTAO_INICIAL_ELEVADOR_2
    request = [DISPOSITIVOREMOTO, 0x06, botao, 1, dado] + converteMatricula(matricula)
    response = scheduler.enviaComando(request, 15)
    if response:
        lista_bytes = list(response)
        if verificaResposta(request, lista_bytes):
            #print(f"Recebida a lista: {lista_bytes}")
            dados_byte_array = response[2:13]
            #print(dados_byte_array)
            return True
    return False
