import pygame
import requests

pygame.mixer.init()
SERVER_ADRESS = ''
SOUND_MOVE = pygame.mixer.Sound('res/music/move.wav')


class ScrollBox:
    # СкроллБокс - виджет для вывода текста с возможностью
    # вертикальной прокрутки
    def __init__(self, x, y, width, height, len_val, font_size):
        self.x = x
        self.y = y
        self.width = width
        self.height = height
        self.len = len_val
        self.text = []
        self.rect = pygame.Rect(x, y, width, height)
        self.font = pygame.font.Font(None, font_size)
        self.active = False
        self.current_text = []
        self.position = 0

    def set_text(self, text):
        self.text = text

    def render(self, screen):
        pygame.draw.rect(screen, (252, 242, 222), self.rect)
        rendered_text = self.render_text()
        for i in rendered_text:
            screen.blit(i[0], i[1])

    def render_text(self):
        rendered_text = []
        if len(self.text) > self.len:
            self.current_text = self.text[self.position:self.len +
                                          self.position - 1]
        else:
            self.current_text = self.text
        for i in range(len(self.current_text)):
            string_rendered = self.font.render(self.current_text[i], 1,
                                               pygame.Color('black'))
            rend_rect = string_rendered.get_rect()
            rend_rect.top = self.y + 10 + i * 30
            rend_rect.left = self.x + 5
            rendered_text.append([string_rendered, rend_rect])
        return rendered_text

    def scroll_up(self):
        if self.position > 0:
            self.position -= 1

    def scroll_down(self):
        if len(self.text) > self.len:
            if self.position < len(self.text) - self.len:
                self.position += 1

    def check_coords(self, pos, button):
        if pos[0] in range(self.x, self.x + self.width):
            if pos[1] in range(self.y, self.y + self.height):
                self.active = True
        if self.active:
            if button == 5:
                self.scroll_down()
            elif button == 4:
                self.scroll_up()


class Board:
    def __init__(self, width, height, color, adress):
        global SERVER_ADRESS
        SERVER_ADRESS = adress
        self.width = width
        self.height = height
        is_white = False
        self.board = [[['', None, False] for __ in range(width)]
                      for _ in range(height)]
        self.selected = None
        self.need_update = None
        for i in range(height):
            is_white = not is_white
            for j in range(width):
                if is_white:
                    self.board[i][j][0] = 'white'
                else:
                    self.board[i][j][0] = 'black'
                is_white = not is_white
        if color == 1:
            self.player = 'w'
            self.opponent = 'b'
            self.numbers = ['8', '7', '6', '5', '4', '3', '2', '1']
            self.letters = ['a', 'b', 'c', 'd', 'e', 'f', 'g', 'h']
        elif color == 2:
            self.numbers = ['1', '2', '3', '4', '5', '6', '7', '8']
            self.letters = ['h', 'g', 'f', 'e', 'd', 'c', 'b', 'a']
            self.player = 'b'
            self.opponent = 'w'

        self.current_turn = 'w'
        self.left = 10
        self.top = 10
        self.cell_size = 30
        self.get_current_turn()
        self.scroll_box = ScrollBox(821, 100, 170, 691, 24, 26)
        self.need_light = False
        self.light_cells = [[0, 0], [0, 0]]
        self.turns = []

    def set_key(self, key):
        self.key = key

    def str_to_num(self, turn):
        # Трансформирует ход вида a2 в координаты
        let = ['a', 'b', 'c', 'd', 'e', 'f', 'g', 'h']
        num = ['8', '7', '6', '5', '4', '3', '2', '1']

        x = self.letters.index(turn[0])
        y = self.numbers.index(turn[1])
        return x, y

    def get_current_turn(self):
        # Получает цвет текущего хода
        current_turn = ''
        try:
            current_turn = requests.get(SERVER_ADRESS +
                                        'get_current_color/{}'.format(
                                            self.key)).text
        except Exception as e:
            pass
        if current_turn in ['w', 'b']:
            self.current_turn = current_turn

    def get_turns(self):
        # Получает историю ходов и выделяет последний ход противника
        try:
            turns = ''
            try:
                turns = requests.get(SERVER_ADRESS + 'get_turns/{}'.format(
                    self.key)).text
            except Exception:
                pass
            if turns != 'error':
                self.turns = turns.split('*')
                self.scroll_box.set_text(turns.split('*'))
                if self.player == 'w' and self.current_turn == 'w':
                    if len(self.turns) > 0 and self.turns[0]:
                        current = self.turns[-1].split(' - ')[1].split('-')
                        x1, y1 = self.str_to_num(current[0])
                        x2, y2 = self.str_to_num(current[1])
                        self.need_light = True
                        self.light_cells[0] = [x1, y1]
                        self.light_cells[1] = [x2, y2]
                elif self.player == 'b' and self.current_turn == 'b':
                    if len(self.turns) > 0 and self.turns[0]:
                        current = self.turns[-1].split(' - ')[0].split('-')
                        x1, y1 = self.str_to_num(current[0][3:])
                        x2, y2 = self.str_to_num(current[1])
                        self.need_light = True
                        self.light_cells[0] = [x1, y1]
                        self.light_cells[1] = [x2, y2]
                elif self.player != self.current_turn:
                    self.need_light = False
        except Exception:
            pass

    def set_view(self, left, top, cell_size):
        self.left = left
        self.top = top
        self.cell_size = cell_size

    def updated(self):
        self.need_update = None

    def set_view(self, left, top, size):
        self.left = left
        self.top = top
        self.cell_size = size

    def change_figure(self, x, y, figure):
        self.board[x][y][1] = figure

    def update_board(self):
        # Загружает положения фигур с сервера
        try:
            new_board = requests.get(SERVER_ADRESS +
                                     'get_board/{}***{}'.format(
                                         self.opponent, self.key)).text
            if len(new_board) and new_board != 'error':
                with open('res/board_temp.txt', 'w') as data:
                    data.write(new_board)
        except Exception:
            pass

    def can_move(self, cell_start, cell_end):
        # Проверка, возиожно ли движение данной фигурой в данную клетку
        try:
            can = requests.get(SERVER_ADRESS +
                               'check_move/{}:{}:{}:{}:{}***{}'.format(
                                   str(cell_start[1]), str(cell_start[0]),
                                   str(cell_end[1]), str(cell_end[0]),
                                   self.player, self.key))
            return True if can.text == '1' else False
        except Exception:
            return False

    def get_update_status(self):
        if self.need_update is None:
            return False
        return True

    def get_update_coords(self):
        return self.need_update

    def move_figure(self, cell_start, cell_end):
        figure = self.board[cell_start[0]][cell_start[1]][1]
        self.change_figure(cell_end[0], cell_end[1], figure)
        self.board[cell_start[0]][cell_start[1]][1] = None
        SOUND_MOVE.play()
        self.need_update = [cell_start, cell_end]

    def get_cell(self, pos):
        pos = [pos[0] - self.left, pos[1] - self.top]
        if pos[0] > 799 or pos[1] > 799:
            return None

        x = pos[0] // self.cell_size
        y = pos[1] // self.cell_size
        return x, y

    def on_click(self, cell):
        # Обрабатывает клик
        figure = self.board[cell[0]][cell[1]]
        old = self.selected
        if not figure[1] is None:
            color = list(figure[1])[0]
            if color == self.player:
                if self.selected is not None and self.selected != cell:
                    self.board[self.selected[1]][self.selected[0]][2] = False
                    self.selected = cell
                    self.board[cell[1]][cell[0]][2] = True
                elif self.selected == cell:
                    self.board[cell[1]][cell[0]][2] = False
                    self.selected = None
                else:
                    self.selected = cell
                    self.board[cell[1]][cell[0]][2] = True
            else:
                if self.selected is not None and\
                   self.can_move(self.selected, cell):
                    self.board[self.selected[1]][self.selected[0]][2] = False
                    self.move_figure(self.selected, cell)
                    self.selected = None
        else:
            if self.selected is not None:
                if self.can_move(self.selected, cell):
                    self.board[self.selected[1]][self.selected[0]][2] = False
                    self.move_figure(self.selected, cell)
                    self.selected = None
                else:
                    self.board[self.selected[1]][self.selected[0]][2] = False
                    self.selected = None

    def get_click(self, pos, button):
        cell = self.get_cell(pos)
        self.scroll_box.check_coords(pos, button)
        if cell is not None and button == 1:
            self.on_click(cell)

    def render(self, screen):
        # Отрисовка элементов
        font = pygame.font.Font(None, 30)
        for i in range(self.height):
            for j in range(self.width):
                pygame.draw.rect(screen, pygame.Color('WHITE'),
                                 (j * self.cell_size + self.left,
                                  i * self.cell_size + self.top,
                                  self.cell_size, self.cell_size), 1)
                if self.board[i][j][0] == 'white':
                    pygame.draw.rect(screen, (214, 198, 180),
                                     (j * self.cell_size + self.left + 1,
                                      i * self.cell_size + self.top + 1,
                                      self.cell_size - 1,
                                      self.cell_size - 1))
                elif self.board[i][j][0] == 'black':
                    pygame.draw.rect(screen, (103, 77, 40),
                                     (j * self.cell_size + self.left + 1,
                                      i * self.cell_size + self.top + 1,
                                      self.cell_size - 1,
                                      self.cell_size - 1))
                if i == self.light_cells[0][1] and\
                   j == self.light_cells[0][0] and self.need_light:
                    pygame.draw.rect(screen, (187, 203, 69),
                                     (j * self.cell_size + self.left + 1,
                                      i * self.cell_size + self.top + 1,
                                      self.cell_size - 1,
                                      self.cell_size - 1))
                if i == self.light_cells[1][1] and\
                   j == self.light_cells[1][0] and self.need_light:
                    pygame.draw.rect(screen, (187, 203, 69),
                                     (j * self.cell_size + self.left + 1,
                                      i * self.cell_size + self.top + 1,
                                      self.cell_size - 1,
                                      self.cell_size - 1))
                if self.board[i][j][2]:
                    pygame.draw.rect(screen, (144, 238, 144),
                                     (j * self.cell_size + self.left + 1,
                                      i * self.cell_size + self.top + 1,
                                      self.cell_size - 3,
                                      self.cell_size - 3), 4)
                if j == 0:
                    string_rendered = font.render(self.numbers[i], 1,
                                                  pygame.Color('black'))
                    num_rect = string_rendered.get_rect()
                    num_rect.top = (i * self.cell_size + self.top +
                                    self.cell_size // 2 -
                                    num_rect.height // 2)
                    num_rect.left = 3
                    screen.blit(string_rendered, num_rect)
                if i == 7:
                    string_rendered = font.render(self.letters[j], 1,
                                                  pygame.Color('black'))
                    let_rect = string_rendered.get_rect()
                    let_rect.left = (j * self.cell_size + self.left +
                                     self.cell_size // 2 -
                                     num_rect.width // 2)
                    let_rect.top = 780
                    screen.blit(string_rendered, let_rect)

        pygame.draw.rect(screen, pygame.Color('WHITE'), (801, 1, 10, 801))
        pygame.draw.rect(screen, pygame.Color(103, 77, 40), (811, 1, 190, 801))
        font = pygame.font.Font(None, 55)
        self.turn_text = ''
        if self.player == self.current_turn:
            self.turn_text = 'Ваш ход'
        else:
            if self.current_turn == 'w':
                self.turn_text = 'Ход белых'
            elif self.current_turn == 'b':
                self.turn_text = 'Ход черных'
        for i in range(2):
            string_rendered = font.render(self.turn_text.split()[i],
                                          1, pygame.Color('black'))
            turn_text_rect = string_rendered.get_rect()
            turn_text_rect.top = 10 + i * 50
            turn_text_rect.left = (190 - turn_text_rect.width) // 2 + 811
            screen.blit(string_rendered, turn_text_rect)
        self.scroll_box.render(screen)
