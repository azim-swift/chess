# settings.py

import os

# Размер клетки в пикселях (будет масштабироваться при полноэкранном режиме)
CELL_SIZE = 100

# Размер доски
BOARD_SIZE = 8

# Цвета
WHITE = (255, 255, 255)
BLACK = (0, 0, 0)
GRAY = (128, 128, 128)
BLUE = (0, 0, 255)
GREEN = (0, 255, 0)
RED = (255, 0, 0)

# Путь к папке с изображениями
ASSETS_PATH = os.path.join(os.path.dirname(__file__), 'assets')

# Глубина поиска AI
AI_DEPTH = 3

# Частота кадров
FPS = 60

# Флаг полноэкранного режима
FULLSCREEN = True  # Установите в True для запуска игры в полноэкранном режиме

# Изначальные размеры окна (будут обновлены в main.py при запуске)
WINDOW_WIDTH = 800
WINDOW_HEIGHT = 800
