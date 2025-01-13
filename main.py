# main.py

import pygame
import sys
import os
import json  # Добавлен импорт json
import settings  # Исправлено: импортируем как модуль
from settings import *
from auth import login, register
from database import initialize_db, get_games_by_user, create_new_game, get_game_by_id
from game import Game, Move
from bot import find_best_move

pygame.init()
pygame.display.set_caption('Шахматный Эндшпиль: Король и Пешка - Король и Пешка')

# Настройка режима отображения
if settings.FULLSCREEN:
    info = pygame.display.Info()
    settings.WINDOW_WIDTH, settings.WINDOW_HEIGHT = info.current_w, info.current_h
    screen = pygame.display.set_mode((settings.WINDOW_WIDTH, settings.WINDOW_HEIGHT), pygame.FULLSCREEN)
    # Масштабирование CELL_SIZE под разрешение экрана
    settings.CELL_SIZE = min(settings.WINDOW_WIDTH, settings.WINDOW_HEIGHT) // settings.BOARD_SIZE
else:
    screen = pygame.display.set_mode((settings.WINDOW_WIDTH, settings.WINDOW_HEIGHT))
    settings.CELL_SIZE = settings.CELL_SIZE  # Используем значение из settings.py

clock = pygame.time.Clock()

def load_images():
    images = {}
    filename_to_key = {
        'king_white.png': 'wK',
        'king_black.png': 'bK',
        'queen_white.png': 'wQ',
        'queen_black.png': 'bQ',
        'pawn_white.png': 'wP',
        'pawn_black.png': 'bP',
        'bishop_white.png': 'wB',
        'bishop_black.png': 'bB',
        'horse_white.png': 'wN',  # Конь
        'horse_black.png': 'bN',  # Конь
        'tower_white.png': 'wR',  # Ладья
        'tower_black.png': 'bR',  # Ладья
        'eye_open.png': 'eye_open',
        'eye_closed.png': 'eye_closed'
    }
    for filename in os.listdir(settings.ASSETS_PATH):
        if filename.endswith('.png'):
            path = os.path.join(settings.ASSETS_PATH, filename)
            key = filename_to_key.get(filename)
            if key:
                try:
                    img = pygame.image.load(path).convert_alpha()
                    # Масштабирование изображения
                    if filename in ['eye_open.png', 'eye_closed.png']:
                        eye_size = 30  # Размер иконки глаза
                        img = pygame.transform.scale(img, (eye_size, eye_size))
                    else:
                        img = pygame.transform.scale(img, (settings.CELL_SIZE, settings.CELL_SIZE))
                    images[key] = img
                    print(f"Загружено изображение: {filename}")
                except pygame.error as e:
                    print(f"Ошибка загрузки изображения {path}: {e}")
            else:
                print(f"Неизвестное изображение: {filename}")
    required_keys = ['wK', 'bK', 'wP', 'bP', 'wQ', 'bQ', 'wR', 'bR', 'wB', 'bB', 'wN', 'bN', 'eye_open', 'eye_closed']
    for key in required_keys:
        if key not in images:
            print(f"Предупреждение: Изображение для {key} не найдено.")
    return images

images = load_images()

def draw_text(win, text, size, color, x, y):
    font = pygame.font.SysFont('Arial', size)
    text_surface = font.render(text, True, color)
    win.blit(text_surface, (x, y))

def auth_screen():
    message = ''
    while True:
        screen.fill(BLACK)
        draw_text(screen, 'Шахматный Эндшпиль', 60, WHITE, settings.WINDOW_WIDTH//2 - 200, 50)
        draw_text(screen, '1. Войти', 40, WHITE, 100, 200)
        draw_text(screen, '2. Зарегистрироваться', 40, WHITE, 100, 300)
        draw_text(screen, '3. Выход', 40, WHITE, 100, 400)
        draw_text(screen, 'Нажмите TAB для переключения между опциями', 20, WHITE, 100, 500)
        draw_text(screen, message, 30, RED, 100, 600)
        pygame.display.flip()
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                pygame.quit()
                sys.exit()
            if event.type == pygame.KEYDOWN:
                if event.key == pygame.K_1:
                    success, msg, user = login_prompt()
                    if success:
                        return user
                    else:
                        message = msg
                if event.key == pygame.K_2:
                    success, msg = register_prompt()
                    message = msg
                if event.key == pygame.K_3:
                    pygame.quit()
                    sys.exit()
        clock.tick(FPS)

def login_prompt():
    username = ''
    password = ''
    input_box = 'username'
    message = ''
    password_visible = False
    eye_icon = images.get('eye_closed')
    eye_rect = pygame.Rect(settings.WINDOW_WIDTH//2 + 150, 300, 30, 30)  # Позиция иконки глаза

    while True:
        screen.fill(BLACK)
        draw_text(screen, 'Вход', 50, WHITE, settings.WINDOW_WIDTH//2 - 80, 50)
        draw_text(screen, 'Имя пользователя:', 35, WHITE, 100, 200)
        draw_text(screen, username, 35, WHITE, 500, 200)
        draw_text(screen, 'Пароль:', 35, WHITE, 100, 300)
        if password_visible:
            display_password = password
        else:
            display_password = '*' * len(password)
        draw_text(screen, display_password, 35, WHITE, 500, 300)
        draw_text(screen, 'Нажмите TAB для переключения между полями ввода', 25, WHITE, 100, 400)
        draw_text(screen, 'Нажмите ESC для возврата в главное меню', 25, WHITE, 100, 450)
        draw_text(screen, message, 30, RED, 100, 500)
        # Подсветка активного поля
        if input_box == 'username':
            pygame.draw.rect(screen, BLUE, pygame.Rect(500, 200, 200, 50), 3)
        else:
            pygame.draw.rect(screen, BLUE, pygame.Rect(500, 300, 200, 50), 3)
        # Рисуем иконку глаза
        if password_visible:
            eye_icon = images.get('eye_open')
        else:
            eye_icon = images.get('eye_closed')
        if eye_icon:
            screen.blit(eye_icon, eye_rect)
        pygame.display.flip()
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                pygame.quit()
                sys.exit()
            if event.type == pygame.MOUSEBUTTONDOWN:
                if eye_rect.collidepoint(event.pos):
                    password_visible = not password_visible
            if event.type == pygame.KEYDOWN:
                if event.key == pygame.K_TAB:
                    input_box = 'password' if input_box == 'username' else 'username'
                elif event.key == pygame.K_ESCAPE:
                    return False, 'Возврат в главное меню.', None
                elif event.key == pygame.K_RETURN:
                    if len(username) < 3 or len(password) < 6:
                        message = 'Имя пользователя ≥ 3 символа, пароль ≥ 6 символов.'
                    else:
                        success, msg, user = login(username, password)
                        if success:
                            return True, msg, user
                        else:
                            message = msg
                elif event.key == pygame.K_BACKSPACE:
                    if input_box == 'username':
                        username = username[:-1]
                    else:
                        password = password[:-1]
                else:
                    if input_box == 'username' and event.unicode.isprintable():
                        username += event.unicode
                    elif input_box == 'password' and event.unicode.isprintable():
                        password += event.unicode
        clock.tick(FPS)

def register_prompt():
    username = ''
    password = ''
    input_box = 'username'
    message = ''
    password_visible = False
    eye_icon = images.get('eye_closed')
    eye_rect = pygame.Rect(settings.WINDOW_WIDTH//2 + 150, 300, 30, 30)  # Позиция иконки глаза

    while True:
        screen.fill(BLACK)
        draw_text(screen, 'Регистрация', 50, WHITE, settings.WINDOW_WIDTH//2 - 120, 50)
        draw_text(screen, 'Имя пользователя:', 35, WHITE, 100, 200)
        draw_text(screen, username, 35, WHITE, 500, 200)
        draw_text(screen, 'Пароль:', 35, WHITE, 100, 300)
        if password_visible:
            display_password = password
        else:
            display_password = '*' * len(password)
        draw_text(screen, display_password, 35, WHITE, 500, 300)
        draw_text(screen, 'Нажмите TAB для переключения между полями ввода', 25, WHITE, 100, 400)
        draw_text(screen, 'Нажмите ESC для возврата в главное меню', 25, WHITE, 100, 450)
        draw_text(screen, message, 30, RED, 100, 500)
        # Подсветка активного поля
        if input_box == 'username':
            pygame.draw.rect(screen, BLUE, pygame.Rect(500, 200, 200, 50), 3)
        else:
            pygame.draw.rect(screen, BLUE, pygame.Rect(500, 300, 200, 50), 3)
        # Рисуем иконку глаза
        if password_visible:
            eye_icon = images.get('eye_open')
        else:
            eye_icon = images.get('eye_closed')
        if eye_icon:
            screen.blit(eye_icon, eye_rect)
        pygame.display.flip()
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                pygame.quit()
                sys.exit()
            if event.type == pygame.MOUSEBUTTONDOWN:
                if eye_rect.collidepoint(event.pos):
                    password_visible = not password_visible
            if event.type == pygame.KEYDOWN:
                if event.key == pygame.K_TAB:
                    input_box = 'password' if input_box == 'username' else 'username'
                elif event.key == pygame.K_ESCAPE:
                    return False, 'Возврат в главное меню.'
                elif event.key == pygame.K_RETURN:
                    if len(username) < 3 or len(password) < 6:
                        message = 'Имя пользователя ≥ 3 символа, пароль ≥ 6 символов.'
                    else:
                        success, msg = register(username, password)
                        if success:
                            message = 'Регистрация успешна. Можете войти.'
                        else:
                            message = msg
                elif event.key == pygame.K_BACKSPACE:
                    if input_box == 'username':
                        username = username[:-1]
                    else:
                        password = password[:-1]
                else:
                    if input_box == 'username' and event.unicode.isprintable():
                        username += event.unicode
                    elif input_box == 'password' and event.unicode.isprintable():
                        password += event.unicode
        clock.tick(FPS)

def select_mode(username):
    message = ''
    while True:
        screen.fill(BLACK)
        draw_text(screen, 'Выберите режим игры', 60, WHITE, settings.WINDOW_WIDTH//2 - 200, 50)
        draw_text(screen, '1. Человек против искусственного интеллекта', 40, WHITE, 100, 200)
        draw_text(screen, '2. Просмотреть текущие игры', 40, WHITE, 100, 300)
        draw_text(screen, '3. Выйти', 40, WHITE, 100, 400)
        draw_text(screen, message, 30, RED, 100, 500)
        pygame.display.flip()
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                pygame.quit()
                sys.exit()
            if event.type == pygame.KEYDOWN:
                if event.key == pygame.K_1:
                    return 'ai'
                if event.key == pygame.K_2:
                    view_games(username)
                if event.key == pygame.K_3:
                    pygame.quit()
                    sys.exit()
        clock.tick(FPS)

def view_games(username):
    games = get_games_by_user(username, status='in_progress')
    selected_game = None
    while True:
        screen.fill(BLACK)
        draw_text(screen, f'Текущие партии пользователя: {username}', 40, WHITE, settings.WINDOW_WIDTH//2 - 250, 50)
        y_offset = 150
        if not games:
            draw_text(screen, 'Нет текущих партий. Начните новую игру.', 30, WHITE, 50, y_offset)
        else:
            for index, game in enumerate(games[:10]):  # Отображаем последние 10 партий
                game_id, white_player, black_player, moves, result, start_time, end_time, status = game
                game_info = f"{index+1}. ID: {game_id} | Белые: {white_player} | Черные: {black_player} | Начало: {start_time}"
                draw_text(screen, game_info, 25, WHITE, 50, y_offset)
                y_offset += 40
                if y_offset > settings.WINDOW_HEIGHT - 100:
                    break
        draw_text(screen, 'Нажмите число партии для возобновления или ESC для возврата', 25, WHITE, 50, settings.WINDOW_HEIGHT - 100)
        pygame.display.flip()
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                pygame.quit()
                sys.exit()
            if event.type == pygame.KEYDOWN:
                if event.key == pygame.K_ESCAPE:
                    return
                elif pygame.K_1 <= event.key <= pygame.K_9:
                    selected_index = event.key - pygame.K_1
                    if selected_index < len(games):
                        selected_game = games[selected_index]
                        resume_game(selected_game)
        clock.tick(FPS)

def resume_game(game):
    game_id, white_player, black_player, moves, result, start_time, end_time, status = game
    game_instance = Game(white_player=white_player, black_player=black_player, game_id=game_id)
    game_screen_instance(game_instance)

def show_game_details(game):
    game_id, white_player, black_player, moves, result, start_time, end_time, status = game
    moves_list = json.loads(moves)  # Преобразование JSON строки обратно в список
    while True:
        screen.fill(BLACK)
        draw_text(screen, f'Партия ID: {game_id}', 40, WHITE, settings.WINDOW_WIDTH//2 - 100, 50)
        draw_text(screen, f"Белые: {white_player} | Черные: {black_player}", 30, WHITE, 50, 100)
        draw_text(screen, f"Результат: {result}", 30, WHITE, 50, 150)
        draw_text(screen, f"Начало: {start_time} | Конец: {end_time}", 30, WHITE, 50, 200)
        draw_text(screen, 'Ходы:', 30, WHITE, 50, 250)
        y_offset = 300
        for i in range(0, len(moves_list), 2):
            move_number = i//2 + 1
            white_move = moves_list[i].get_chess_notation()
            black_move = moves_list[i+1].get_chess_notation() if i+1 < len(moves_list) else ''
            move_text = f"{move_number}. {white_move} {black_move}"
            draw_text(screen, move_text, 25, WHITE, 50, y_offset)
            y_offset += 30
            if y_offset > settings.WINDOW_HEIGHT - 100:
                break
        draw_text(screen, 'Нажмите ESC для возврата к списку партий', 25, WHITE, 50, settings.WINDOW_HEIGHT - 50)
        pygame.display.flip()
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                pygame.quit()
                sys.exit()
            if event.type == pygame.KEYDOWN:
                if event.key == pygame.K_ESCAPE:
                    return
        clock.tick(FPS)

def game_screen_instance(game_instance):
    selected_square = None
    valid_moves = []
    run = True
    paused = False

    while run:
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                run = False
                pygame.quit()
                sys.exit()
            elif event.type == pygame.KEYDOWN:
                if event.key == pygame.K_p:
                    paused = not paused
            elif event.type == pygame.MOUSEBUTTONDOWN:
                if not paused and not game_instance.checkmate and not game_instance.stalemate:
                    pos = pygame.mouse.get_pos()
                    row, col = pos[1] // settings.CELL_SIZE, pos[0] // settings.CELL_SIZE
                    piece = game_instance.board[row][col]
                    if selected_square:
                        # Ищем соответствующий объект Move из valid_moves
                        selected_move = None
                        for m in valid_moves:
                            if m.end_row == row and m.end_col == col:
                                selected_move = m
                                break

                        if selected_move and game_instance.is_move_valid(selected_move):
                            game_instance.make_move(selected_move)
                            selected_square = None
                            valid_moves = []
                            # Если игра против ИИ и ход после этого принадлежит ИИ
                            if (isinstance(game_instance.black_player, str) and
                                game_instance.black_player.lower() == 'ai' and
                                not game_instance.white_to_move and
                                not game_instance.checkmate and
                                not game_instance.stalemate):
                                ai_move = find_best_move(game_instance, depth=settings.AI_DEPTH)
                                if ai_move:
                                    game_instance.make_move(ai_move)
                        else:
                            # Если ход некорректен, сбрасываем выбор
                            if piece != '--' and ((game_instance.white_to_move and piece[0] == 'w') or (not game_instance.white_to_move and piece[0] == 'b')):
                                selected_square = (row, col)
                                valid_moves = game_instance.get_piece_moves(row, col)
                            else:
                                selected_square = None
                                valid_moves = []
                    else:
                        if piece != '--' and ((game_instance.white_to_move and piece[0] == 'w') or (not game_instance.white_to_move and piece[0] == 'b')):
                            selected_square = (row, col)
                            valid_moves = game_instance.get_piece_moves(row, col)

        if not paused:
            screen.fill(BLACK)
            game_instance.draw(screen, images, selected_square, valid_moves)
        else:
            # Показать паузу
            screen.fill(GRAY)
            draw_text(screen, 'Пауза', 60, WHITE, settings.WINDOW_WIDTH//2 - 100, settings.WINDOW_HEIGHT//2 - 50)
            draw_text(screen, 'Нажмите S для сохранения и выхода', 30, WHITE, settings.WINDOW_WIDTH//2 - 150, settings.WINDOW_HEIGHT//2 + 20)
            draw_text(screen, 'Нажмите P для продолжения игры', 30, WHITE, settings.WINDOW_WIDTH//2 - 150, settings.WINDOW_HEIGHT//2 + 60)

            # Проверка событий в паузе
            for event in pygame.event.get():
                if event.type == pygame.QUIT:
                    pygame.quit()
                    sys.exit()
                elif event.type == pygame.KEYDOWN:
                    if event.key == pygame.K_s:
                        # Сохранить и выйти в главное меню
                        run = False
                    elif event.key == pygame.K_p:
                        paused = False

        pygame.display.flip()
        clock.tick(FPS)

        if not paused and (game_instance.checkmate or game_instance.stalemate):
            # Отображение результата уже происходит в draw_game_state
            # Добавим задержку перед возвратом в главное меню
            pygame.time.delay(5000)
            run = False
            # Если игра завершена, обновляем статус
            if game_instance.result:
                game_instance.save_game_completion()

def game_screen(mode, white_player='White', black_player='AI'):
    # Создание новой игры или загрузка существующей
    if mode == 'ai':
        if black_player.lower() == 'ai':
            game_id = create_new_game(white_player, 'AI')
            game_instance = Game(white_player=white_player, black_player='AI', game_id=game_id)
        else:
            game_id = create_new_game(white_player, black_player)
            game_instance = Game(white_player=white_player, black_player=black_player, game_id=game_id)
    run_game = True
    while run_game:
        game_screen_instance(game_instance)
        run_game = False  # После завершения игры возвращаемся к выбору режима

def main():
    initialize_db()  # Инициализация базы данных при запуске приложения
    current_user = auth_screen()
    if current_user:
        mode = select_mode(current_user)
        if mode == 'ai':
            game_screen(mode, white_player=current_user, black_player='AI')

if __name__ == '__main__':
    main()
