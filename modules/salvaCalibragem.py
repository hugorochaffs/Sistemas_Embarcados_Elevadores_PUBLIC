import os
import pickle
import variables
import socket

def get_hostname():
    variables.hostname = socket.gethostname()
    return variables.hostname

# Função para salvar as variáveis de calibragem
def salvar_calibragem(file_name):
    calibragem = {
        'POS_TERREO_E1': variables.POS_TERREO_E1,
        'POS_ANDAR1_E1': variables.POS_ANDAR1_E1,
        'POS_ANDAR2_E1': variables.POS_ANDAR2_E1,
        'POS_ANDAR3_E1': variables.POS_ANDAR3_E1,
        'BSD_TERREO_E1': variables.BSD_TERREO_E1,
        'BSD_ANDAR1_E1': variables.BSD_ANDAR1_E1,
        'BSD_ANDAR2_E1': variables.BSD_ANDAR2_E1,
        'BSD_ANDAR3_E1': variables.BSD_ANDAR3_E1,
        'POS_TERREO_E2': variables.POS_TERREO_E2,
        'POS_ANDAR1_E2': variables.POS_ANDAR1_E2,
        'POS_ANDAR2_E2': variables.POS_ANDAR2_E2,
        'POS_ANDAR3_E2': variables.POS_ANDAR3_E2,
        'BSD_TERREO_E2': variables.BSD_TERREO_E2,
        'BSD_ANDAR1_E2': variables.BSD_ANDAR1_E2,
        'BSD_ANDAR2_E2': variables.BSD_ANDAR2_E2,
        'BSD_ANDAR3_E2': variables.BSD_ANDAR3_E2
    }
    with open(file_name, 'wb') as file:
        pickle.dump(calibragem, file)

# Função para carregar as variáveis de calibragem
def carregar_calibragem(file_name):
    if os.path.exists(file_name):
        with open(file_name, 'rb') as file:
            calibragem = pickle.load(file)
            # Atualiza as variáveis globais
            variables.POS_TERREO_E1 = calibragem['POS_TERREO_E1']
            variables.POS_ANDAR1_E1 = calibragem['POS_ANDAR1_E1']
            variables.POS_ANDAR2_E1 = calibragem['POS_ANDAR2_E1']
            variables.POS_ANDAR3_E1 = calibragem['POS_ANDAR3_E1']
            variables.BSD_TERREO_E1 = calibragem['BSD_TERREO_E1']
            variables.BSD_ANDAR1_E1 = calibragem['BSD_ANDAR1_E1']
            variables.BSD_ANDAR2_E1 = calibragem['BSD_ANDAR2_E1']
            variables.BSD_ANDAR3_E1 = calibragem['BSD_ANDAR3_E1']
            variables.POS_TERREO_E2 = calibragem['POS_TERREO_E2']
            variables.POS_ANDAR1_E2 = calibragem['POS_ANDAR1_E2']
            variables.POS_ANDAR2_E2 = calibragem['POS_ANDAR2_E2']
            variables.POS_ANDAR3_E2 = calibragem['POS_ANDAR3_E2']
            variables.BSD_TERREO_E2 = calibragem['BSD_TERREO_E2']
            variables.BSD_ANDAR1_E2 = calibragem['BSD_ANDAR1_E2']
            variables.BSD_ANDAR2_E2 = calibragem['BSD_ANDAR2_E2']
            variables.BSD_ANDAR3_E2 = calibragem['BSD_ANDAR3_E2']
            return True
    return False