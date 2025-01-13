# database.py

import sqlite3
import os
from datetime import datetime
import json

DATABASE_FILE = 'chess.db'

def get_connection():
    conn = sqlite3.connect(DATABASE_FILE)
    return conn

def initialize_db():
    conn = get_connection()
    cursor = conn.cursor()

    # Создание таблицы пользователей (если еще не существует)
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS users (
            username TEXT PRIMARY KEY,
            password_hash TEXT NOT NULL
        )
    ''')

    # Создание таблицы партий
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS games (
            game_id INTEGER PRIMARY KEY AUTOINCREMENT,
            white_player TEXT NOT NULL,
            black_player TEXT NOT NULL,
            moves TEXT NOT NULL,  -- Сохранение ходов в формате JSON
            result TEXT,
            start_time TEXT,
            end_time TEXT,
            status TEXT NOT NULL,  -- 'in_progress' или 'completed'
            FOREIGN KEY (white_player) REFERENCES users(username),
            FOREIGN KEY (black_player) REFERENCES users(username)
        )
    ''')

    conn.commit()
    conn.close()

def save_user(username, password_hash):
    conn = get_connection()
    cursor = conn.cursor()
    try:
        cursor.execute('INSERT INTO users (username, password_hash) VALUES (?, ?)', (username, password_hash))
        conn.commit()
        return True, 'Пользователь успешно зарегистрирован.'
    except sqlite3.IntegrityError:
        return False, 'Пользователь уже существует.'
    finally:
        conn.close()

def get_user(username):
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute('SELECT * FROM users WHERE username = ?', (username,))
    user = cursor.fetchone()
    conn.close()
    return user

def create_new_game(white_player, black_player):
    conn = get_connection()
    cursor = conn.cursor()
    start_time = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
    moves_json = json.dumps([])
    cursor.execute('''
        INSERT INTO games (white_player, black_player, moves, result, start_time, end_time, status)
        VALUES (?, ?, ?, ?, ?, ?, ?)
    ''', (white_player, black_player, moves_json, None, start_time, None, 'in_progress'))
    game_id = cursor.lastrowid
    conn.commit()
    conn.close()
    return game_id

def update_game(game_id, moves, result=None, end_time=None, status='in_progress'):
    conn = get_connection()
    cursor = conn.cursor()
    moves_json = json.dumps(moves)
    cursor.execute('''
        UPDATE games
        SET moves = ?, result = ?, end_time = ?, status = ?
        WHERE game_id = ?
    ''', (moves_json, result, end_time, status, game_id))
    conn.commit()
    conn.close()

def get_games_by_user(username, status=None):
    conn = get_connection()
    cursor = conn.cursor()
    if status:
        cursor.execute('''
            SELECT * FROM games 
            WHERE (white_player = ? OR black_player = ?) AND status = ?
            ORDER BY start_time DESC
        ''', (username, username, status))
    else:
        cursor.execute('''
            SELECT * FROM games 
            WHERE white_player = ? OR black_player = ?
            ORDER BY start_time DESC
        ''', (username, username))
    games = cursor.fetchall()
    conn.close()
    return games

def get_game_by_id(game_id):
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute('SELECT * FROM games WHERE game_id = ?', (game_id,))
    game = cursor.fetchone()
    conn.close()
    return game
