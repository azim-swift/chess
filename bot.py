# ai.py

import math
import random
from game import Move


def find_best_move(game, depth):
    best_move = None
    if game.white_to_move:
        best_value = -math.inf
        for move in game.get_valid_moves():
            game.make_move(move, update_state=False)
            move_value = minimax(game, depth - 1, -math.inf, math.inf, False)
            game.undo_move()
            if move_value > best_value:
                best_value = move_value
                best_move = move
    else:
        best_value = math.inf
        for move in game.get_valid_moves():
            game.make_move(move, update_state=False)
            move_value = minimax(game, depth - 1, -math.inf, math.inf, True)
            game.undo_move()
            if move_value < best_value:
                best_value = move_value
                best_move = move

    print(f"AI выбрал ход: {best_move.get_chess_notation() if best_move else 'Нет доступных ходов'}")
    return best_move


def minimax(game, depth, alpha, beta, is_maximizing):
    if depth == 0 or game.checkmate or game.stalemate:
        return evaluate_game(game)

    if is_maximizing:
        max_eval = -math.inf
        for move in game.get_valid_moves():
            game.make_move(move, update_state=False)
            eval = minimax(game, depth - 1, alpha, beta, False)
            game.undo_move()
            max_eval = max(max_eval, eval)
            alpha = max(alpha, eval)
            if beta <= alpha:
                break
        return max_eval
    else:
        min_eval = math.inf
        for move in game.get_valid_moves():
            game.make_move(move, update_state=False)
            eval = minimax(game, depth - 1, alpha, beta, True)
            game.undo_move()
            min_eval = min(min_eval, eval)
            beta = min(beta, eval)
            if beta <= alpha:
                break
        return min_eval


def evaluate_game(game):
    # Если мат, возвращаем максимальную или минимальную оценку
    if game.checkmate:
        if game.white_to_move:
            return -math.inf  # Белые проиграли
        else:
            return math.inf   # Черные выиграли

    # Оценка позиции на основе материала
    piece_values = {'K': 0, 'Q': 9, 'R': 5, 'B': 3, 'N': 3, 'P': 1}
    white_score = 0
    black_score = 0

    for row in game.board:
        for piece in row:
            if piece != '--':
                value = piece_values.get(piece[1], 0)
                if piece[0] == 'w':
                    white_score += value
                else:
                    black_score += value

    # Оценка контроля центра
    center_squares = [(3, 3), (3, 4), (4, 3), (4, 4)]
    for (r, c) in center_squares:
        piece = game.board[r][c]
        if piece != '--':
            if piece[0] == 'w':
                white_score += 0.1
            else:
                black_score += 0.1

    # Оценка безопасности короля
    white_king_pos = game.find_king('w')
    black_king_pos = game.find_king('b')
    if white_king_pos:
        white_score -= 0.1 * len(game.get_piece_moves(*white_king_pos))
    if black_king_pos:
        black_score -= 0.1 * len(game.get_piece_moves(*black_king_pos))

    # Оценка активности фигур
    for r in range(8):
        for c in range(8):
            piece = game.board[r][c]
            if piece != '--':
                moves = game.get_piece_moves(r, c)
                if piece[0] == 'w':
                    white_score += 0.05 * len(moves)
                else:
                    black_score += 0.05 * len(moves)

    # Добавление случайного фактора для разнообразия ходов
    random_factor = random.uniform(-0.5, 0.5)
    evaluation = (white_score - black_score) + random_factor
    print(f"Оценка позиции: {evaluation} (Белые: {white_score}, Черные: {black_score})")
    return evaluation