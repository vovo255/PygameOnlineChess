import pygame
import sys
import os
import requests
import math
import time
import random
from board import Board

FPS = 30
SIZE = WIDTH, HEIGHT = 1001, 801
COLOR = None
GET_ACT_TIMER = 30
FIGURE_WIDTH = FIGURE_HEIGHT = 80
SERVER_ADRESS = 'http://178.76.236.166:1654/'

pygame.init()
pygame.mixer.music.load('res/music/background.mp3')
pygame.mixer.music.play(-1)
clock = pygame.time.Clock()
screen = pygame.display.set_mode(SIZE)
board = None
figures_sprites = pygame.sprite.Group()
player_key = None
screen_rect = (0, 0, WIDTH, HEIGHT)
sprites_star = pygame.sprite.Group()
first_in = True


def terminate():
    # Выход из игры. По необходимости завершает текущую сессию
    if player_key is not None:
        try:
            requests.get(SERVER_ADRESS + 'close_session/{}'.format(player_key))
        except Exception:
            pass
    pygame.quit()
    sys.exit()


def load_image(name, colorkey=None):
    fullname = os.path.join('res/pictures/', name)
    image = pygame.image.load(fullname)
    if colorkey is not None:
        if colorkey == -1:
            colorkey = image.get_at((0, 0))
        image.set_colorkey(colorkey)
    else:
        image = image.convert_alpha()
    return image


def board_init():
    global board
    board = Board(8, 8, COLOR, SERVER_ADRESS)
    board.set_view(1, 1, 100)


figure_images = {'bB': load_image('bB.png'),
                 'bK': load_image('bK.png'),
                 'bN': load_image('bN.png'),
                 'bP': load_image('bP.png'),
                 'bQ': load_image('bQ.png'),
                 'bR': load_image('bR.png'),
                 'wB': load_image('wB.png'),
                 'wK': load_image('wK.png'),
                 'wN': load_image('wN.png'),
                 'wP': load_image('wP.png'),
                 'wQ': load_image('wQ.png'),
                 'wR': load_image('wR.png')}


class Figure(pygame.sprite.Sprite):
    # Шахматные фигуры
    def __init__(self, figure_type, pos_x, pos_y, group):
        super().__init__(group)
        self.x = pos_x
        self.y = pos_y
        self.image = figure_images[figure_type]
        self.rect = self.image.get_rect()
        self.rect = self.rect.move(FIGURE_WIDTH * pos_x + 20 * pos_x + 10,
                                   FIGURE_HEIGHT * pos_y + 20 * pos_y + 10)

    def update_coords(self, new_coords):
        pos_x = new_coords[0]
        pos_y = new_coords[1]
        self.x = new_coords[0]
        self.y = new_coords[1]
        self.rect = self.image.get_rect()
        self.rect = self.rect.move(FIGURE_WIDTH * pos_x + 20 * pos_x + 10,
                                   FIGURE_HEIGHT * pos_y + 20 * pos_y + 10)

    def get_coords(self):
        return self.x, self.y


def load_level(filename):
    filename = "res/" + filename
    with open(filename, 'r') as mapFile:
        level_map = [line.strip().split('-') for line in mapFile]
    max_width = max(map(len, level_map))
    return level_map


def generate_level(level):
    for y in range(len(level)):
        for x in range(len(level[y])):
            if level[y][x] != '.':
                Figure(level[y][x], x, y, figures_sprites)
                board.change_figure(x, y, level[y][x])


def make_board():
    if COLOR == 1:
        generate_level(load_level('map_white.txt'))
    elif COLOR == 2:
        generate_level(load_level('map_black.txt'))


def update_board():
    # Обновление положения фигур на поле
    global figures_sprites
    try:
        bord = load_level('board_temp.txt')
        figures_sprites = pygame.sprite.Group()
        generate_level(bord)
    except Exception:
        pass


def get_text_rendered(text, coords, size, is_center=False,
                      background=True, italic=False):
    # Возвращает отрендеренный текст
    font = pygame.font.Font(None, size)
    font.set_italic(italic)
    if background:
        text_rendered = font.render(text, 1, (194, 107, 16), (255, 255, 255))
    else:
        text_rendered = font.render(text, 1, (194, 107, 16))
    text_rect = text_rendered.get_rect()
    text_rect.top = coords[1]
    if is_center:
        text_rect.x = (WIDTH - text_rect.width) // 2
    else:
        text_rect.x = coords[0]
    return text_rendered, text_rect


class Button:
    # Виджет кнопки
    def __init__(self, x, y, x_step, y_step, width, height, text, font_size):
        self.x = x
        self.y = y
        self.width = width
        self.height = height
        self.text = text
        self.button = pygame.Rect(x, y, width, height)
        self.rendered_text = get_text_rendered(text,
                                               (x + x_step, y + y_step),
                                               font_size, background=False)
        self.contur = pygame.Rect(x - 3, y - 3, width + 6, height + 6)

    def render(self, screen):
        pygame.draw.rect(screen, (101, 67, 33), self.contur, 5)
        pygame.draw.rect(screen, (255, 255, 255), self.button)
        screen.blit(*self.rendered_text)

    def check_coords(self, coords):
        if coords[0] in range(self.x, self.x + self.width):
            if coords[1] in range(self.y, self.y + self.height):
                return True
        return False


class TextInput:
    # Виджет текстового ввода. Есть возможность сделать вводимый текст
    # скрытым, например, если это пароль
    def __init__(self, x, y, width, height, font_size, max_len, hide=False):
        self.is_selected = False
        self.x = x
        self.y = y
        self.text = ''
        self.width = width
        self.height = height
        self.font_size = font_size
        self.hide = hide
        self.rendered_text = get_text_rendered(self.text, (x, y),
                                               font_size, background=True)
        self.line = pygame.Rect(self.x, self.y + self.height, self.width, 2)
        self.contur = pygame.Rect(x - 3, y - 3, width + 6, height + 6)
        self.max_len = max_len

    def render(self, screen):
        if self.is_selected:
            pygame.draw.rect(screen, (101, 67, 33), self.contur)
        pygame.draw.rect(screen, (101, 67, 33), self.line)
        screen.blit(*self.rendered_text)

    def update(self, key):
        if self.is_selected:
            try:
                char = key.unicode
                if char.isalnum():
                    if self.max_len > len(self.text):
                        self.text += char
                else:
                    if ord(char) == 8:
                        if len(self.text) > 0:
                            self.text = self.text[:-1]
            except Exception:
                pass
        if self.hide:
            self.rendered_text = get_text_rendered('*' * len(self.text),
                                                   (self.x, self.y),
                                                   self.font_size,
                                                   background=True)
        else:
            self.rendered_text = get_text_rendered(self.text,
                                                   (self.x, self.y),
                                                   self.font_size,
                                                   background=True)

    def check_coords(self, coords):
        if coords[0] in range(self.x, self.x + self.width):
            if coords[1] in range(self.y, self.y + self.height):
                self.is_selected = True
            else:
                self.is_selected = False
        else:
            self.is_selected = False

    def clear(self):
        self.text = ''
        self.rendered_text = get_text_rendered('',
                                               (self.x, self.y),
                                               self.font_size,
                                               background=True)

    def get_text(self):
        return self.text


class Particle(pygame.sprite.Sprite):
    # Частицы. Отображаются при выигрыще партии
    fire = [load_image("star.png")]
    for scale in (5, 10, 20):
        fire.append(pygame.transform.scale(fire[0], (scale, scale)))

    def __init__(self, pos, dx, dy):
        super().__init__(sprites_star)
        self.image = random.choice(self.fire)
        self.rect = self.image.get_rect()
        self.velocity = [dx, dy]
        self.rect.x, self.rect.y = pos
        self.gravity = 1

    def update(self):
        self.velocity[1] += self.gravity
        self.rect.x += self.velocity[0]
        self.rect.y += self.velocity[1]
        if not self.rect.colliderect(screen_rect):
            self.kill()


def create_particles(position):
    # Генерация частиц
    particle_count = 600
    numbers = range(-50, 50)
    for _ in range(particle_count):
        Particle(position, random.choice(numbers), random.choice(numbers))


def register(login, passwd):
    # Создание нового пользователя
    try:
        ok = requests.get(SERVER_ADRESS +
                          'register_user/{}\n{}'.format(login, passwd)).text
        if ok == 'error':
            return False, 'errorName'
        return True, ok
    except Exception:
        return False, 'errorConnect'


def login_user(login, passwd):
    # Вход в игру существующего пользователя
    try:
        key = requests.get(SERVER_ADRESS +
                           'login_user/{}\n{}'.format(login, passwd)).text
        if key == 'error':
            return False, 'errorData'
        return True, key
    except Exception:
        return False, 'errorConnect'


def get_rating():
    # Загрузка рейтинга пользователя с сервера
    rating = requests.get(SERVER_ADRESS +
                          'get_rating/{}'.format(player_key)).text
    if rating == 'error':
        print("Ошибка получения рейтинга!")
        return ''
    return rating


def find_opponent():
    # Поиск оппонента
    global COLOR

    try:
        board_is = requests.get(SERVER_ADRESS +
                                'check_board_is/{}'.format(player_key)).text
        if board_is == 'OK':
            COLOR = int(requests.get(SERVER_ADRESS +
                                     'get_color/{}'.format(player_key)).text)
            return True

        create = requests.get(SERVER_ADRESS +
                              'create_board/{}'.format(player_key)).text
        if create == 'OK':
            COLOR = int(requests.get(SERVER_ADRESS +
                                     'get_color/{}'.format(player_key)).text)
            return True
    except Exception:
        pass
    return False


def check_result():
    # Проверка результата партии
    result = requests.get(SERVER_ADRESS +
                          'check_result/{}'.format(player_key)).text
    if result not in ['False', 'error']:
        if result == 'WIN':
            return 1
        elif result == 'LOSS':
            return 2
        elif result == 'None':
            return 3
    else:
        return False


def start_screen():
    # Экран приветствия
    hello_text = 'Вас приветствует игра Онлайн шахматы!'
    name_developer_text = 'Игру разработал Владимир Алексеев'
    nickname_developer_text = 'Github nickname: vovo255'
    fon = pygame.transform.scale(load_image('fon.jpg'), (WIDTH, HEIGHT))
    screen.blit(fon, (0, 0))
    screen.blit(*get_text_rendered(hello_text, (0, 30), 60, True))
    screen.blit(*get_text_rendered(name_developer_text,
                                   (10, 700), 50, italic=True))
    screen.blit(*get_text_rendered(nickname_developer_text,
                                   (10, 750), 50, italic=True))

    while True:
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                terminate()
            elif (event.type == pygame.KEYDOWN or
                  event.type == pygame.MOUSEBUTTONDOWN):
                return
        pygame.display.flip()
        clock.tick(FPS)


def login_screen():
    # Экран входа в игру
    global player_key
    error_type = 0
    main_text = 'Войдите в игру или зарегистрируйтесь:'
    login_indicator_text = 'Логин:'
    pass_indicator_text = 'Пароль:'
    register_login_error = 'Пользователь с таким именем уже существует!'
    login_data_error = 'Пользователя с таким именем и паролем не найдено!'
    server_connect_error = 'Отсутствует соединение с сервером!'
    login_button = Button(400, 600, 35, 7, 200, 50, 'Войти', 60)
    register_button = Button(375, 670, 23, 15, 250, 50,
                             'Зарегистрироваться', 30)
    login_input = TextInput(400, 450, 200, 30, 40, 13)
    pass_input = TextInput(400, 550, 200, 30, 40, 13, True)
    while True:
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                terminate()
            elif event.type == pygame.MOUSEBUTTONDOWN:
                key = event.button
                pos = event.pos
                if key == 1:
                    login = login_button.check_coords(pos)
                    reg = register_button.check_coords(pos)
                    login_input.check_coords(pos)
                    pass_input.check_coords(pos)
                    if reg:
                        if login_input.get_text() and pass_input.get_text():
                            ok = register(login_input.get_text(),
                                          pass_input.get_text())
                            if ok[0]:
                                player_key = ok[1]
                                return
                            else:
                                if ok[1] == 'errorName':
                                    error_type = 1
                                elif ok[1] == 'errorConnect':
                                    error_type = 10
                                login_input.clear()
                                pass_input.clear()
                    elif login:
                        if login_input.get_text() and pass_input.get_text():
                            ok = login_user(login_input.get_text(),
                                            pass_input.get_text())
                            if ok[0]:
                                player_key = ok[1]
                                return
                            else:
                                if ok[1] == 'errorData':
                                    error_type = 2
                                elif ok[1] == 'errorConnect':
                                    error_type = 10
                                login_input.clear()
                                pass_input.clear()

            elif event.type == pygame.KEYDOWN:
                login_input.update(event)
                pass_input.update(event)

        screen.fill((0, 0, 0))
        fon = pygame.transform.scale(load_image('fon.jpg'), (WIDTH, HEIGHT))
        screen.blit(fon, (0, 0))
        screen.blit(*get_text_rendered(main_text, (0, 30), 49, True))
        screen.blit(*get_text_rendered(login_indicator_text, (0, 400),
                                       49, True))
        screen.blit(*get_text_rendered(pass_indicator_text, (0, 500),
                                       49, True))
        login_button.render(screen)
        register_button.render(screen)
        login_input.render(screen)
        pass_input.render(screen)
        if error_type == 1:
            screen.blit(*get_text_rendered(register_login_error, (0, 730),
                                           49, True))
        elif error_type == 2:
            screen.blit(*get_text_rendered(login_data_error, (0, 730),
                                           40, True))
        elif error_type == 10:
            screen.blit(*get_text_rendered(server_connect_error, (0, 730),
                                           40, True))
        pygame.display.flip()
        clock.tick(FPS)


def menu_screen():
    # Главное меню
    get_rating()
    rating_indicator_text = 'Ваш рейтинг:'
    rating_text = get_rating()
    start_game_button = Button(395, 300, 5, 5, 210, 43, 'Начать игру', 49)
    exit_prog_button = Button(370, 400, 5, 5, 260, 43, 'Выйти из игры', 49)
    while True:
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                terminate()
            elif event.type == pygame.MOUSEBUTTONDOWN:
                key = event.button
                pos = event.pos
                if key == 1:
                    exit_game = exit_prog_button.check_coords(pos)
                    start_game = start_game_button.check_coords(pos)
                    if exit_game:
                        terminate()
                    if start_game:
                        return
        screen.fill((0, 0, 0))
        fon = pygame.transform.scale(load_image('fon.jpg'), (WIDTH, HEIGHT))
        screen.blit(fon, (0, 0))
        screen.blit(*get_text_rendered(rating_indicator_text, (30, 30), 49))
        screen.blit(*get_text_rendered(rating_text, (270, 30), 49))
        start_game_button.render(screen)
        exit_prog_button.render(screen)
        pygame.display.flip()
        clock.tick(FPS)


def finding_opponent_screen():
    # Экран с анимацией во время поиска оппонента
    earth = load_image('earth.jpg')
    lupa = load_image('lupa.png')
    x = 0
    lupa_circle = 0
    R = 150
    act = 0
    search_indicator_text = 'Поиск противника... Таймаут:'
    cancel_button = Button(440, 720, 10, 7, 120, 40, 'Отмена', 40)
    search_time_text = '60'
    start_time = time.time()
    pygame.time.set_timer(GET_ACT_TIMER, 1000)
    while True:
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                terminate()
            if event.type == GET_ACT_TIMER:
                ok = find_opponent()
                if ok:
                    return True
            if event.type == pygame.MOUSEBUTTONDOWN:
                key = event.button
                pos = event.pos
                cancel_search = cancel_button.check_coords(pos)
                if cancel_search:
                    return False
        if time.time() - start_time > 59:
            return False
        screen.fill((0, 0, 0))
        rel_x = x % earth.get_rect().width
        screen.blit(earth, (rel_x - earth.get_rect().width, 0))
        if rel_x < WIDTH:
            screen.blit(earth, (rel_x, 0))
        x -= 2
        lupa_x = int(R * math.cos(math.radians(lupa_circle)) + 250)
        lupa_y = int(R * math.sin(math.radians(lupa_circle)) + 250)
        lupa_circle += 2
        search_time_text = str(int(60 - (time.time() - start_time)))
        screen.blit(lupa, (lupa_x, lupa_y))
        screen.blit(*get_text_rendered(search_indicator_text, (20, 20), 49))
        screen.blit(*get_text_rendered(search_time_text, (550, 20), 49))
        cancel_button.render(screen)
        pygame.display.flip()
        clock.tick(FPS)


def game_end_screen(mode):
    # Экран окончания партии
    star = False
    is_first = True
    fon = pygame.transform.scale(load_image('game_end.jpg'), (WIDTH, HEIGHT))
    partion_end_text = 'Партия окончена!'
    exit_menu_button = Button(375, 700, 5, 5, 250, 43, 'Главное меню', 49)
    if mode == 3:
        game_end_text = 'Ничья!'
    elif mode == 1:
        game_end_text = 'Вы выиграли!'
        star = True
    elif mode == 2:
        game_end_text = 'Вы проиграли!'

    while True:
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                terminate()
            elif event.type == pygame.MOUSEBUTTONDOWN:
                exit_menu = exit_menu_button.check_coords(event.pos)
                if exit_menu:
                    return
        if star and is_first:
            is_first = False
            create_particles((500, 400))

        screen.fill((0, 0, 0))
        screen.blit(fon, (0, 0))
        screen.blit(*get_text_rendered(partion_end_text, (30, 30), 49, True))
        screen.blit(*get_text_rendered(game_end_text, (270, 100), 49, True))
        exit_menu_button.render(screen)
        sprites_star.update()
        sprites_star.draw(screen)
        pygame.display.flip()
        clock.tick(FPS)


def main_game():
    # Главный цикл
    board_init()
    board.set_key(player_key)
    make_board()
    running = True

    pygame.time.set_timer(GET_ACT_TIMER, 1000)
    while running:
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                terminate()
            if event.type == pygame.MOUSEBUTTONDOWN:
                board.get_click(event.pos, event.button)
            if event.type == GET_ACT_TIMER:
                result = check_result()
                if result:
                    game_end_screen(result)
                    return
                board.update_board()
                board.get_current_turn()
                board.get_turns()
                update_board()

        if board.get_update_status():
            coords = board.get_update_coords()
            if coords is not None:
                sprites = figures_sprites.sprites()
                for i in range(len(sprites)):
                    if sprites[i].get_coords() == coords[1]:
                            figures_sprites.remove(sprites[i])
                            board.updated()
                for i in range(len(sprites)):
                    if sprites[i].get_coords() == coords[0]:
                            sprites[i].update_coords(coords[1])
                            board.updated()
            board.need_update = None

        screen.fill((0, 0, 0))
        board.render(screen)
        figures_sprites.draw(screen)
        pygame.display.flip()


start_screen()
login_screen()
while True:
    if not first_in:
        pygame.mixer.music.play(-1)
    while True:
        menu_screen()
        ok = finding_opponent_screen()
        if ok:
            break
    pygame.mixer.music.stop()
    main_game()
    first_in = False
