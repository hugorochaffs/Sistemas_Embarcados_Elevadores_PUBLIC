import Adafruit_SSD1306
from PIL import Image, ImageDraw, ImageFont
import time
import variables

# Configurações do display OLED
RST = 24  # Ajuste se necessário
OLED_ADDRESS = 0x3C
DISPLAY_WIDTH = 128
DISPLAY_HEIGHT = 64

# Inicializa o display
def tentaIniciarOLED():
    for tentativa in range(20):
        print(f"Tentativa {tentativa + 1} para iniciar o display OLED...")
        if initialize_display():
            variables.useOled = True
            return
        time.sleep(0.5)
    
    print("Não foi possível iniciar o display OLED após 20 tentativas.")
    variables.useOled = False

def initialize_display():
    try:
        global disp
        disp = Adafruit_SSD1306.SSD1306_128_64(rst=RST)
        disp.begin()
        disp.clear()
        disp.display()

        global image
        global draw
        image = Image.new('1', (DISPLAY_WIDTH, DISPLAY_HEIGHT))
        draw = ImageDraw.Draw(image)

        global font_large
        global font_med
        global font_small
        try:
            font_large = ImageFont.truetype('/fontes/DejaVuSans-Bold.ttf', 12)
            font_med = ImageFont.truetype('/fontes/DejaVuSans-Bold.ttf', 10)
            font_small = ImageFont.truetype('/fontes/DejaVuSans-Bold.ttf', 8)
        except IOError:
            print("Erro: Não foi possível carregar as fontes.")
            return False

        print("Display inicializado com sucesso.")
        return True
    except ImportError:
        print("Erro: Biblioteca Adafruit_SSD1306 não encontrada. Instale-a usando 'pip install Adafruit-SSD1306'.")
        return False
    except Exception as e:
        print(f"Erro ao inicializar o display: {e}")
        return False

def draw_arrow(draw, x, y, direction):
    if direction == 1:
        draw.polygon([(x, y+14), (x+8, y), (x+14, y+14)], outline=255, fill=255)
    elif direction == 2:
        draw.polygon([(x, y), (x+8, y+14), (x+14, y)], outline=255, fill=255)
    elif direction == 3:
        draw.rectangle([x, y, x+14, y+14], outline=255, fill=255)

def draw_elevator(draw, x_offset, elevator_num, direction, floor, temperature):
    half_width = DISPLAY_WIDTH // 2
    section_x = x_offset * half_width
    arrow_x = section_x + 48
    arrow_y = 16
    text_y = 40
    temp_y = 50

    draw.text((section_x+3 , text_y-40), f'Elev_{elevator_num}', font=font_large, fill=255)
    draw_arrow(draw, arrow_x, arrow_y, direction)
    draw.text((section_x + 5, text_y-5), f'Andar: {floor}', font=font_large, fill=255)
    draw.text((section_x + 5, temp_y), f'Temp: {temperature:.1f}C', font=font_small, fill=255)

    if direction == 1:
        draw.text((section_x + 5, 15), 'Sobe', font=font_large, fill=255)
    elif direction == 2:
        draw.text((section_x + 5, 15), 'Desce', font=font_large, fill=255)
    else:
        draw.text((section_x + 5, 15), 'Parado', font=font_med, fill=255)

def update_display(elevator1, elevator2):
        try:
            draw.rectangle((0, 0, DISPLAY_WIDTH, DISPLAY_HEIGHT), outline=0, fill=0)  # Limpa a tela

            separation_x = (DISPLAY_WIDTH * 0.5) + (DISPLAY_WIDTH * 0.01)  # 5% para a direita
            draw.line((separation_x, 0, separation_x, DISPLAY_HEIGHT), fill=255)

            draw_elevator(draw, 0, 1, elevator1['direction'], elevator1['floor'], elevator1['temperature'])
            draw_elevator(draw, 1, 2, elevator2['direction'], elevator2['floor'], elevator2['temperature'])

            disp.image(image)
            disp.display()


        except OSError as e:
            ...

        except Exception as e:
            ...

def end_display():
    disp.clear()
    disp.display()
    print("OLED desligado!")
