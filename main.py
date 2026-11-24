import pygame
import math
import random
import sys

from expression import Expression, TokenizationError, ParserSyntaxError
from token import Token, TokenType

# консты экрана
WIDTH, HEIGHT = 1000, 700
INPUT_BOX_WIDTH = 400
INPUT_BOX_HEIGHT = 40
PADDING = 20

# цвета
BG_COLOR = (240, 240, 240)  # заглушка для фона
AXIS_COLOR = (50, 50, 50)
GRID_COLOR = (220, 220, 220)
FUNCTION_COLOR = (255, 0, 0)
INPUT_BOX_COLOR_INACTIVE = (200, 200, 200)
INPUT_BOX_COLOR_ACTIVE = (100, 100, 255)
TEXT_COLOR = (0, 0, 0)

# настройки ДСК
X_MIN, X_MAX = -10, 10
Y_MIN, Y_MAX = -10, 10

# настройки точек
MAX_POINTS_ON_FIELD = 3
POINT_TOLERANCE = 0.3
POINT_LIFETIME = 15.0       
POINT_X_MIN, POINT_X_MAX = -8, 8
POINT_Y_MIN, POINT_Y_MAX = -8, 8

# переменные состояния игры
score = 0
points_list = []

# инициализация
pygame.init()
screen = pygame.display.set_mode((WIDTH, HEIGHT), pygame.FULLSCREEN | pygame.SCALED)
pygame.display.set_caption("function_fight")
clock = pygame.time.Clock()
font = pygame.font.Font(None, 24)
input_font = pygame.font.Font(None, 32)

backspace_hole = 0

# настройки текстового поля
# RULES_TITLE = Правила игры:"
# RULES_BODY = (
#     "1. Введите формулу f(x).\n"
#     "2. График должен пройти через оранжевую точку.\n"
#     "3. Число внутри точки — ваши очки.\n"
#     "4. Нажмите Enter для проверки."
# )

# rules_title_surf = font.render(RULES_TITLE, True, (50, 50, 50))
# rules_body_surf = font.render(RULES_BODY, True, (80, 80, 80))

# RULES_X = PADDING
# RULES_Y = PADDING

# настройки поля ввода
input_box = pygame.Rect(PADDING, HEIGHT - INPUT_BOX_HEIGHT - PADDING, INPUT_BOX_WIDTH, INPUT_BOX_HEIGHT)
color_inactive = INPUT_BOX_COLOR_INACTIVE
color_active = INPUT_BOX_COLOR_ACTIVE
color = color_inactive
active = False
text = ''
cursor_pos = 0
expr = None
cursor_visible = True
cursor_timer = 0

# бесполезные приколы
last_key_time = 0
KEY_REPEAT_DELAY = 0.0

def cartesian_to_screen(x, y):
    # переводит ДК в пиксели
    # масштаб по осям
    scale_x = (WIDTH - 2 * PADDING - INPUT_BOX_WIDTH - PADDING) / (X_MAX - X_MIN)
    scale_y = (HEIGHT - 2 * PADDING - INPUT_BOX_HEIGHT - PADDING) / (Y_MAX - Y_MIN)
    
    screen_x = PADDING + (x - X_MIN) * scale_x
    screen_y = PADDING + (Y_MAX - y) * scale_y
    
    return int(screen_x), int(screen_y)

def draw_axes():
    # отрисовка ДСК
    scale_x = (WIDTH - 2 * PADDING - INPUT_BOX_WIDTH - PADDING) / (X_MAX - X_MIN)
    scale_y = (HEIGHT - 2 * PADDING - INPUT_BOX_HEIGHT - PADDING) / (Y_MAX - Y_MIN)
    
    for i in range(int(X_MIN), int(X_MAX) + 1):
        x, _ = cartesian_to_screen(i, 0)
        pygame.draw.line(screen, GRID_COLOR, (x, PADDING), (x, HEIGHT - PADDING - INPUT_BOX_HEIGHT - PADDING), 1) # отрисовка сетки по y
    
    for i in range(int(Y_MIN), int(Y_MAX) + 1):
        _, y = cartesian_to_screen(0, i)
        pygame.draw.line(screen, GRID_COLOR, (PADDING, y), (WIDTH - PADDING - PADDING - 400, y), 1) # отрисовка сетки по x

    zero_x, zero_y = cartesian_to_screen(0, 0)
    
    pygame.draw.line(screen, AXIS_COLOR, (PADDING, zero_y), (WIDTH - PADDING - PADDING - 400, zero_y), 2) # отрисовка Ox
    pygame.draw.polygon(screen, AXIS_COLOR, [(WIDTH - PADDING - PADDING - 390, zero_y), 
                                             (WIDTH - PADDING - PADDING - 400, zero_y - 5), 
                                             (WIDTH - PADDING - PADDING - 400, zero_y + 5)]) # отрисовка стрелочки
    
    pygame.draw.line(screen, AXIS_COLOR, (zero_x, PADDING), (zero_x, HEIGHT - PADDING - INPUT_BOX_HEIGHT - PADDING), 2) # отрисовка Oy
    pygame.draw.polygon(screen, AXIS_COLOR, [(zero_x, PADDING - 10), 
                                             (zero_x - 5, PADDING), 
                                             (zero_x + 5, PADDING)])

    for i in range(int(X_MIN), int(X_MAX) + 1):
        if i == 0: continue
        x, y = cartesian_to_screen(i, 0)
        pygame.draw.line(screen, AXIS_COLOR, (x, y - 5), (x, y + 5), 2)
        txt = font.render(str(i), True, TEXT_COLOR)
        screen.blit(txt, (x - txt.get_width() // 2, y + 10)) # отрисовка чисел, отметок на осях

    for i in range(int(Y_MIN), int(Y_MAX) + 1):
        if i == 0: continue
        x, y = cartesian_to_screen(0, i)
        pygame.draw.line(screen, AXIS_COLOR, (x - 5, y), (x + 5, y), 2)
        txt = font.render(str(i), True, TEXT_COLOR)
        screen.blit(txt, (x - txt.get_width() - 10, y - txt.get_height() // 2))

class PointValue: # тут и так всё ясно
    def __init__(self, x, y, value):
        self.x = x
        self.y = y
        self.value = value
        self.spawn_time = pygame.time.get_ticks() / 1000

    def draw(self, surface):
        sx, sy = cartesian_to_screen(self.x, self.y)
        
        pygame.draw.circle(surface, (255, 215, 0), (sx, sy), 12)
        pygame.draw.circle(surface, (255, 69, 0), (sx, sy), 10)
        
        value_text = font.render(str(self.value), True, (255, 255, 255))
        surface.blit(value_text, (sx - value_text.get_width() // 2, sy - value_text.get_height() // 2))

    def is_expired(self, current_time):
        return current_time - self.spawn_time > POINT_LIFETIME

def spawn_point():
    if len(points_list) < MAX_POINTS_ON_FIELD:
        x = random.randint(POINT_X_MIN * 10, POINT_X_MAX * 10) / 10.0
        y = random.randint(POINT_Y_MIN * 10, POINT_Y_MAX * 10) / 10.0
        value = random.randint(10, 50)
        points_list.append(PointValue(x, y, value))

def draw_function(func_str):
    # Отрисовка графика
    if not func_str or func_str.strip() == '':
        return
    
    points = []
    
    for screen_x in range(PADDING, WIDTH - PADDING - PADDING - 400):
        scale_x = (WIDTH - 2 * PADDING - INPUT_BOX_WIDTH - PADDING) / (X_MAX - X_MIN)
        x = X_MIN + (screen_x - PADDING) / scale_x
        
        try:
            if expr is not None:
                y = expr.eval(x)
            else:
                y = None
            
            if y is None:
                continue
                
            if Y_MIN <= y <= Y_MAX:
                screen_y = PADDING + (Y_MAX - y) * ((HEIGHT - 2 * PADDING - INPUT_BOX_HEIGHT - PADDING) / (Y_MAX - Y_MIN))
                points.append((screen_x, int(screen_y)))
        except (ValueError, ZeroDivisionError, OverflowError, SyntaxError, NameError, TypeError):
            continue
            
    if len(points) > 1:
        pygame.draw.lines(screen, FUNCTION_COLOR, False, points, 2)

def get_mouse_coords():
    # по приколу, чтобы было
    mx, my = pygame.mouse.get_pos()
    if PADDING < mx < WIDTH - PADDING - PADDING and PADDING < my < HEIGHT - PADDING - INPUT_BOX_HEIGHT - PADDING:
        scale_x = (WIDTH - 2 * PADDING - INPUT_BOX_WIDTH - PADDING) / (X_MAX - X_MIN)
        scale_y = (HEIGHT - 2 * PADDING - INPUT_BOX_HEIGHT - PADDING) / (Y_MAX - Y_MIN)
        
        x = X_MIN + (mx - PADDING) / scale_x
        y = Y_MAX - (my - PADDING) / scale_y
        return x, y
    return None

# основной цикл
running = True
background = pygame.image.load('assets/void_var.png').convert()
background = pygame.transform.scale(background, (WIDTH, HEIGHT))
while running:
    dt = clock.tick(60) / 1000
    if not points_list:
        for _ in range(MAX_POINTS_ON_FIELD):
            spawn_point()

    current_time = pygame.time.get_ticks() / 1000

    points_to_expire = [p for p in points_list if p.is_expired(current_time)]
    
    for p in points_to_expire:
        if p in points_list:
            points_list.remove(p)
            spawn_point()

    for event in pygame.event.get():
        if event.type == pygame.QUIT:
            running = False
            
        if event.type == pygame.MOUSEBUTTONDOWN:
            if input_box.collidepoint(event.pos):
                active = True
            else:
                active = False
            color = color_active if active else color_inactive
            
        if event.type == pygame.KEYDOWN:
            if active:
                current_time = pygame.time.get_ticks() / 1000
                
                if current_time - last_key_time < KEY_REPEAT_DELAY and event.key != pygame.K_BACKSPACE and event.key != pygame.K_RETURN:
                    continue
                last_key_time = current_time

                if event.key == pygame.K_RETURN:
                    if not text.strip():
                        continue

                    points_to_remove = []
                    for point in points_list[:]:
                        eval_x = point.x
                        
                        try:
                            if expr is not None:
                                y_calc = expr.eval(eval_x)
                            
                            if y_calc is None or not isinstance(y_calc, (int, float)):
                                continue
                            
                            if abs(y_calc - point.y) <= POINT_TOLERANCE:
                                func_lower = text.lower()
                                if "x^3" in func_lower or "x**3" in func_lower:
                                    multiplier = 3
                                elif "x^2" in func_lower or "x**2" in func_lower:
                                    multiplier = 2
                                elif "x" in func_lower:
                                    multiplier = 1
                                else:
                                    multiplier = 1
                                
                                score += point.value * multiplier
                                
                                points_to_remove.append(point)
                                
                                
                                
                                print(f"Попадание! Множитель: x{multiplier}")
                                print(f"Очки: +{point.value * multiplier}. Всего: {score}")
                        
                        except (ValueError, ZeroDivisionError, OverflowError, SyntaxError, NameError, TypeError):
                            continue
                    
                    for p in points_to_remove:
                        if p in points_list:
                            points_list.remove(p)
                            spawn_point()

                elif event.key == pygame.K_BACKSPACE:
                    backspace_hole = 1
                    if cursor_pos > 0:
                        text = text[:cursor_pos - 1] + text[cursor_pos:]
                        cursor_pos -= 1
                elif event.key == pygame.K_ESCAPE:
                    text = ''
                elif event.key == pygame.K_LEFT:
                    cursor_pos = max(0, cursor_pos - 1)
                elif event.key == pygame.K_RIGHT:
                    cursor_pos = min(len(text), cursor_pos + 1)
                else:
                    allowed_chars = "x0123456789+-*/()., xX^ "
                    if event.unicode and event.unicode in allowed_chars:
                        char = event.unicode.replace(',', '.').lower()
                        text = text[:cursor_pos] + char + text[cursor_pos:]
                        cursor_pos += 1

        if event.type == pygame.KEYUP:
            if event.key == pygame.K_BACKSPACE:
                backspace_hole = 0
    try:
        expr = Expression(text)
    except Exception:
        expr = None

    if backspace_hole > 0:
        backspace_hole += 1
    if backspace_hole > 25:
        if cursor_pos > 0:
            text = text[:cursor_pos - 1] + text[cursor_pos:]
            cursor_pos -= 1
        backspace_hole -= 2


    cursor_timer += dt
    if cursor_timer > 0.5:
        cursor_visible = not cursor_visible
        cursor_timer = 0

    # отрисовка

    # screen.fill(BG_COLOR)
    screen.blit(background, (0, 0))
    
    mouse_coords = get_mouse_coords()
    if mouse_coords:
        hint_text = font.render(f"x: {mouse_coords[0]:.2f}, y: {mouse_coords[1]:.2f}", True, TEXT_COLOR)
        screen.blit(hint_text, (PADDING, PADDING))

    # screen.blit(rules_title_surf, (RULES_X, RULES_Y))
    # screen.blit(rules_body_surf, (RULES_X, RULES_Y + rules_title_surf.get_height() + 5))

    draw_axes()
    draw_function(text)
    
    # поле ввода
    txt_surface = input_font.render(text, True, TEXT_COLOR)
    width = max(INPUT_BOX_WIDTH, txt_surface.get_width() + 10)
    input_box.w = width
    screen.blit(txt_surface, (input_box.x + 5, input_box.y + 5))
    pygame.draw.rect(screen, color, input_box, 2)

    if active and cursor_visible:
        prefix_width = input_font.size(text[:cursor_pos])[0]
        cursor_x = input_box.x + 5 + prefix_width
        cursor_y1 = input_box.y + 5
        cursor_y2 = input_box.y + input_box.height - 5
        pygame.draw.line(screen, TEXT_COLOR, (cursor_x, cursor_y1), (cursor_x, cursor_y2), 2)

    # отрисовка счёта
    score_text = font.render(f"Очки: {score}", True, (0, 0, 0))
    score_x = input_box.x + input_box.width + 20
    score_y = input_box.y + (input_box.height - score_text.get_height()) // 2
    screen.blit(score_text, (score_x, score_y))

    # отрисовка точек
    for point in points_list:
        point.draw(screen)

    pygame.display.flip()

pygame.quit()
sys.exit()