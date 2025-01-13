# auth.py

import bcrypt
from database import save_user, get_user


def register(username, password):
    if len(username) < 3 or len(password) < 6:
        return False, 'Имя пользователя должно быть не менее 3 символов, а пароль - не менее 6.'

    # Проверка, существует ли уже пользователь
    user = get_user(username)
    if user:
        return False, 'Пользователь уже существует.'

    # Хеширование пароля
    hashed = bcrypt.hashpw(password.encode('utf-8'), bcrypt.gensalt()).decode('utf-8')

    # Сохранение пользователя в базе данных
    success, msg = save_user(username, hashed)
    return success, msg


def login(username, password):
    user = get_user(username)
    if not user:
        return False, 'Пользователь не найден.', None

    stored_hash = user[1].encode('utf-8')  # Предполагается, что второй столбец - password_hash
    if bcrypt.checkpw(password.encode('utf-8'), stored_hash):
        return True, 'Вход успешен.', username
    else:
        return False, 'Неверный пароль.', None
