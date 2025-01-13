# game.py

import pygame
import settings
from settings import *
from copy import deepcopy
from datetime import datetime
from database import update_game, get_game_by_id
import json


class Move:
    def __init__(self, start_pos, end_pos, piece_moved, piece_captured, is_pawn_promotion=False, promotion_choice='Q'):
        self.start_row, self.start_col = start_pos
        self.end_row, self.end_col = end_pos
        self.piece_moved = piece_moved
        self.piece_captured = piece_captured
        self.is_pawn_promotion = is_pawn_promotion
        self.promotion_choice = promotion_choice

    def __eq__(self, other):
        if isinstance(other, Move):
            return (self.start_row == other.start_row and
                    self.start_col == other.start_col and
                    self.end_row == other.end_row and
                    self.end_col == other.end_col and
                    self.piece_moved == other.piece_moved and
                    self.piece_captured == other.piece_captured and
                    self.is_pawn_promotion == other.is_pawn_promotion and
                    self.promotion_choice == other.promotion_choice)
        return False

    def get_chess_notation(self):
        cols_to_files = {0: 'a', 1: 'b', 2: 'c', 3: 'd',
                         4: 'e', 5: 'f', 6: 'g', 7: 'h'}
        return cols_to_files[self.start_col] + str(8 - self.start_row) + \
               cols_to_files[self.end_col] + str(8 - self.end_row)

    def to_dict(self):
        return {
            'start_pos': [self.start_row, self.start_col],
            'end_pos': [self.end_row, self.end_col],
            'piece_moved': self.piece_moved,
            'piece_captured': self.piece_captured,
            'is_pawn_promotion': self.is_pawn_promotion,
            'promotion_choice': self.promotion_choice
        }

    @classmethod
    def from_dict(cls, move_dict):
        return cls(
            start_pos=tuple(move_dict['start_pos']),
            end_pos=tuple(move_dict['end_pos']),
            piece_moved=move_dict['piece_moved'],
            piece_captured=move_dict['piece_captured'],
            is_pawn_promotion=move_dict['is_pawn_promotion'],
            promotion_choice=move_dict.get('promotion_choice', 'Q')
        )


class Game:
    def __init__(self, white_player='White', black_player='AI', game_id=None):
        self.white_player = white_player
        self.black_player = black_player
        self.game_id = game_id
        if game_id:
            self.load_game(game_id)
        else:
            self.board = self.create_initial_board()
            self.white_to_move = True
            self.move_log = []
            self.selected_square = None
            self.valid_moves = []
            self.checkmate = False
            self.stalemate = False
            self.en_passant_possible = ()
            self.promotion_choice = 'Q'
            self.start_time = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
            self.end_time = None
            self.result = None

    def create_initial_board(self):
        # Начальная расстановка: белые - король и слон, черные - король и ладья
        board = [['--' for _ in range(8)] for _ in range(8)]
        board[7][4] = 'wK'  # Белый король на e1
        board[7][2] = 'wB'  # Белый слон на c1
        board[0][4] = 'bK'  # Черный король на e8
        board[0][7] = 'bR'  # Черная ладья на h8
        return board

    def load_game(self, game_id):
        game = get_game_by_id(game_id)
        if game:
            _, white_player, black_player, moves, result, start_time, end_time, status = game
            self.white_player = white_player
            self.black_player = black_player
            self.move_log = [Move.from_dict(move_dict) for move_dict in json.loads(moves)]
            self.reconstruct_board()
            self.result = result
            self.start_time = start_time
            self.end_time = end_time
            self.checkmate = status == 'completed' and ('checkmate' in (result.lower()) if result else False)
            self.stalemate = status == 'completed' and ('stalemate' in (result.lower()) if result else False)
            self.white_to_move = len(self.move_log) % 2 == 0
        else:
            print(f"Игра с ID {game_id} не найдена.")
            self.board = self.create_initial_board()
            self.white_to_move = True
            self.move_log = []
            self.selected_square = None
            self.valid_moves = []
            self.checkmate = False
            self.stalemate = False
            self.en_passant_possible = ()
            self.promotion_choice = 'Q'
            self.start_time = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
            self.end_time = None
            self.result = None

    def reconstruct_board(self):
        self.board = self.create_initial_board()
        for move in self.move_log:
            self.board[move.start_row][move.start_col] = '--'
            self.board[move.end_row][move.end_col] = move.piece_moved
            if move.is_pawn_promotion:
                self.board[move.end_row][move.end_col] = move.piece_moved[0] + move.promotion_choice

    def make_move(self, move, update_state=True):
        self.board[move.start_row][move.start_col] = '--'
        self.board[move.end_row][move.end_col] = move.piece_moved
        self.move_log.append(move)
        self.white_to_move = not self.white_to_move
        if update_state:
            self.check_game_state()
            self.save_current_game()

    def undo_move(self):
        if self.move_log:
            move = self.move_log.pop()
            self.board[move.start_row][move.start_col] = move.piece_moved
            self.board[move.end_row][move.end_col] = move.piece_captured
            self.white_to_move = not self.white_to_move
            self.check_game_state()
            self.save_current_game()

    def get_valid_moves(self):
        moves = self.get_all_possible_moves()
        valid_moves = []
        for move in moves:
            game_copy = deepcopy(self)
            game_copy.make_move(move, update_state=False)
            if not game_copy.in_check(not self.white_to_move) and not game_copy.kings_too_close():
                valid_moves.append(move)
        return valid_moves

    def kings_too_close(self):
        white_king_pos = self.find_king('w')
        black_king_pos = self.find_king('b')
        if white_king_pos is None or black_king_pos is None:
            return False
        return abs(white_king_pos[0] - black_king_pos[0]) <= 1 and abs(white_king_pos[1] - black_king_pos[1]) <= 1

    def get_all_possible_moves(self):
        moves = []
        for r in range(8):
            for c in range(8):
                piece = self.board[r][c]
                if piece == '--':
                    continue
                if self.white_to_move and piece[0] != 'w':
                    continue
                if not self.white_to_move and piece[0] != 'b':
                    continue
                piece_type = piece[1]
                if piece_type == 'K':
                    self.get_king_moves(r, c, moves)
                elif piece_type == 'R':
                    self.get_rook_moves(r, c, moves)
                elif piece_type == 'B':
                    self.get_bishop_moves(r, c, moves)
                elif piece_type == 'Q':
                    self.get_queen_moves(r, c, moves)
                elif piece_type == 'N':
                    self.get_knight_moves(r, c, moves)
        return moves

    def get_king_moves(self, r, c, moves):
        directions = [(-1, -1), (-1, 0), (-1, 1),
                      (0, -1), (0, 1),
                      (1, -1), (1, 0), (1, 1)]
        ally_color = 'w' if self.white_to_move else 'b'

        for dr, dc in directions:
            end_row, end_col = r + dr, c + dc
            if 0 <= end_row < 8 and 0 <= end_col < 8:
                target = self.board[end_row][end_col]
                if target == '--' or target[0] != ally_color:
                    if not self.is_square_under_attack(end_row, end_col, ally_color):
                        moves.append(Move((r, c), (end_row, end_col), self.board[r][c], target))

    def get_rook_moves(self, r, c, moves):
        directions = [(-1, 0), (1, 0), (0, -1), (0, 1)]
        ally_color = 'w' if self.white_to_move else 'b'

        for dr, dc in directions:
            end_row, end_col = r + dr, c + dc
            while 0 <= end_row < 8 and 0 <= end_col < 8:
                target = self.board[end_row][end_col]
                if target == '--':
                    moves.append(Move((r, c), (end_row, end_col), self.board[r][c], target))
                else:
                    if target[0] != ally_color:
                        moves.append(Move((r, c), (end_row, end_col), self.board[r][c], target))
                    break
                end_row += dr
                end_col += dc

    def get_bishop_moves(self, r, c, moves):
        directions = [(-1, -1), (-1, 1), (1, -1), (1, 1)]
        ally_color = 'w' if self.white_to_move else 'b'

        for dr, dc in directions:
            end_row, end_col = r + dr, c + dc
            while 0 <= end_row < 8 and 0 <= end_col < 8:
                target = self.board[end_row][end_col]
                if target == '--':
                    moves.append(Move((r, c), (end_row, end_col), self.board[r][c], target))
                else:
                    if target[0] != ally_color:
                        moves.append(Move((r, c), (end_row, end_col), self.board[r][c], target))
                    break
                end_row += dr
                end_col += dc

    def get_knight_moves(self, r, c, moves):
        knight_moves = [(-2, -1), (-1, -2), (-2, 1), (-1, 2),
                        (1, -2), (2, -1), (1, 2), (2, 1)]
        ally_color = 'w' if self.white_to_move else 'b'

        for dr, dc in knight_moves:
            end_row, end_col = r + dr, c + dc
            if 0 <= end_row < 8 and 0 <= end_col < 8:
                target = self.board[end_row][end_col]
                if target == '--' or target[0] != ally_color:
                    moves.append(Move((r, c), (end_row, end_col), self.board[r][c], target))

    def is_square_under_attack(self, row, col, ally_color, board=None):
        if board is None:
            board = self.board

        enemy_color = 'b' if ally_color == 'w' else 'w'

        # Проверка атакующих ладей и ферзей (по горизонтали и вертикали)
        directions = [(-1, 0), (1, 0), (0, -1), (0, 1)]
        for dr, dc in directions:
            r, c = row + dr, col + dc
            while 0 <= r < 8 and 0 <= c < 8:
                piece = board[r][c]
                if piece == '--':
                    r += dr
                    c += dc
                    continue
                if piece[0] == enemy_color:
                    if piece[1] in ['R', 'Q']:
                        return True
                    else:
                        break
                else:
                    break
                r += dr
                c += dc

        # Проверка атакующих слонов и ферзей (по диагонали)
        directions = [(-1, -1), (-1, 1), (1, -1), (1, 1)]
        for dr, dc in directions:
            r, c = row + dr, col + dc
            while 0 <= r < 8 and 0 <= c < 8:
                piece = board[r][c]
                if piece == '--':
                    r += dr
                    c += dc
                    continue
                if piece[0] == enemy_color:
                    if piece[1] in ['B', 'Q']:
                        return True
                    else:
                        break
                else:
                    break
                r += dr
                c += dc

        return False   

    def in_check(self, white_to_move):
        king_pos = self.find_king('w' if white_to_move else 'b')
        if king_pos is None:
            return True
        return self.is_square_under_attack(king_pos[0], king_pos[1], 'w' if white_to_move else 'b')

    def find_king(self, color):
        for r in range(8):
            for c in range(8):
                piece = self.board[r][c]
                if piece != '--' and piece[1] == 'K' and piece[0] == color:
                    return (r, c)
        return None

    def check_game_state(self):
        if self.in_check(self.white_to_move):
            if not self.get_valid_moves():
                self.checkmate = True
                self.stalemate = False
                self.result = 'Black wins by checkmate' if self.white_to_move else 'White wins by checkmate'
                self.end_time = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
                self.update_game_status('completed')
            else:
                self.checkmate = False
                self.stalemate = False
        else:
            if not self.get_valid_moves():
                self.stalemate = True
                self.checkmate = False
                self.result = 'Draw by stalemate'
                self.end_time = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
                self.update_game_status('completed')
            elif self.is_only_kings():
                self.stalemate = True
                self.result = 'Draw by insufficient material'
                self.end_time = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
                self.update_game_status('completed')
            else:
                self.stalemate = False
                self.checkmate = False

    def is_only_kings(self):
        return all(piece == '--' or piece[1] == 'K' for row in self.board for piece in row)

    def update_game_status(self, status):
        if self.game_id:
            update_game(
                game_id=self.game_id,
                moves=[move.to_dict() for move in self.move_log],
                result=self.result,
                end_time=self.end_time,
                status=status
            )

    def save_current_game(self):
        if self.game_id:
            update_game(
                game_id=self.game_id,
                moves=[move.to_dict() for move in self.move_log],
                result=self.result,
                end_time=self.end_time,
                status='completed' if self.result else 'in_progress'
            )

    def save_game_completion(self):
        if self.game_id and self.result:
            update_game(
                game_id=self.game_id,
                moves=[move.to_dict() for move in self.move_log],
                result=self.result,
                end_time=self.end_time,
                status='completed'
            )
            self.export_pgn()

    def export_pgn(self):
        if not self.game_id:
            return
        pgn_content = f"[Event \"Chess Endgame\"]\n"
        pgn_content += f"[Site \"Local\"]\n"
        pgn_content += f"[Date \"{self.start_time.split(' ')[0]}\"]\n"
        pgn_content += f"[Round \"-\"]\n"
        pgn_content += f"[White \"{self.white_player}\"]\n"
        pgn_content += f"[Black \"{self.black_player}\"]\n"
        pgn_content += f"[Result \"{self.result}\"]\n\n"

        move_text = ''
        for i in range(0, len(self.move_log), 2):
            move_number = i // 2 + 1
            white_move = self.move_log[i].get_chess_notation()
            black_move = self.move_log[i + 1].get_chess_notation() if i + 1 < len(self.move_log) else ''
            move_text += f"{move_number}. {white_move} {black_move} "
        move_text += self.result
        pgn_content += move_text

        pgn_filename = f"game_{self.start_time.replace(':', '-').replace(' ', '_')}_id_{self.game_id}.pgn"
        with open(pgn_filename, 'w') as f:
            f.write(pgn_content)

    def draw(self, win, images, selected_square=None, valid_moves=None):
        self.draw_board(win, selected_square, valid_moves)
        self.draw_pieces(win, images)
        self.draw_game_state(win)

    def draw_board(self, win, selected_square, valid_moves):
        colors = [WHITE, GRAY]
        for r in range(8):
            for c in range(8):
                color = colors[(r + c) % 2]
                pygame.draw.rect(win, color, pygame.Rect(c * settings.CELL_SIZE, r * settings.CELL_SIZE, settings.CELL_SIZE, settings.CELL_SIZE))
                if selected_square and (r, c) == selected_square:
                    pygame.draw.rect(win, BLUE, pygame.Rect(c * settings.CELL_SIZE, r * settings.CELL_SIZE, settings.CELL_SIZE, settings.CELL_SIZE), 3)
                if valid_moves:
                    for move in valid_moves:
                        if move.end_row == r and move.end_col == c:
                            center = (c * settings.CELL_SIZE + settings.CELL_SIZE // 2, r * settings.CELL_SIZE + settings.CELL_SIZE // 2)
                            pygame.draw.circle(win, GREEN, center, 10)

    def draw_pieces(self, win, images):
        for r in range(8):
            for c in range(8):
                piece = self.board[r][c]
                if piece != '--':
                    img = images.get(piece)
                    if img:
                        win.blit(img, pygame.Rect(c * settings.CELL_SIZE, r * settings.CELL_SIZE, settings.CELL_SIZE, settings.CELL_SIZE))
                    else:
                        print(f"Изображение для {piece} не найдено. Проверьте наличие файла и правильность названия.")

    def draw_game_state(self, win):
        if self.checkmate:
            font = pygame.font.SysFont('Arial', 36)
            text = font.render('Шах и мат!', True, RED)
            win.blit(text, (settings.WINDOW_WIDTH // 2 - text.get_width() // 2, settings.WINDOW_HEIGHT // 2 - text.get_height() // 2))
        elif self.stalemate:
            font = pygame.font.SysFont('Arial', 36)
            text = font.render('Пат!', True, RED)
            win.blit(text, (settings.WINDOW_WIDTH // 2 - text.get_width() // 2, settings.WINDOW_HEIGHT // 2 - text.get_height() // 2))
        elif self.in_check(self.white_to_move):
            font = pygame.font.SysFont('Arial', 24)
            text = font.render('Шах!', True, RED)
            win.blit(text, (10, 10))

    def is_move_valid(self, move):
        return move in self.get_valid_moves()

    def get_piece_moves(self, r, c):
        piece = self.board[r][c]
        if piece == '--':
            return []
        if self.white_to_move and piece[0] != 'w':
            return []
        if not self.white_to_move and piece[0] != 'b':
            return []
        moves = []
        piece_type = piece[1]
        if piece_type == 'K':
            self.get_king_moves(r, c, moves)
        elif piece_type == 'R':
            self.get_rook_moves(r, c, moves)
        elif piece_type == 'B':
            self.get_bishop_moves(r, c, moves)
        elif piece_type == 'Q':
            self.get_queen_moves(r, c, moves)
        elif piece_type == 'N':
            self.get_knight_moves(r, c, moves)
        valid_moves = []
        for move in moves:
            game_copy = deepcopy(self)
            game_copy.make_move(move, update_state=False)
            if not game_copy.in_check(not self.white_to_move) and not game_copy.kings_too_close():
                valid_moves.append(move)
        return valid_moves