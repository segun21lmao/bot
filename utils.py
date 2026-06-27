import json
from pathlib import Path

# Загружаем словарь один раз при импорте (кэшируем)
_BLOCK_MAP = None

def _load_block_map():
    """Загружает сопоставление русских названий и английских ID из ru_blocks.json"""
    global _BLOCK_MAP
    if _BLOCK_MAP is not None:
        return _BLOCK_MAP

    json_path = Path(__file__).parent / "ru_blocks.json"
    try:
        with open(json_path, "r", encoding="utf-8") as f:
            data = json.load(f)
        # Приводим все ключи к нижнему регистру для удобства поиска
        _BLOCK_MAP = {key.lower(): value for key, value in data.items()}
    except (FileNotFoundError, json.JSONDecodeError):
        # Если файл отсутствует или повреждён, используем пустой словарь
        _BLOCK_MAP = {}
    return _BLOCK_MAP


def get_block_name(title: str) -> str:
    """
    Возвращает английский идентификатор блока по русскому названию.
    Если точное совпадение не найдено, возвращает "chest".
    """
    if not title:
        return "chest"

    block_map = _load_block_map()
    title_lower = title.lower().strip()

    # Точное совпадение
    if title_lower in block_map:
        return block_map[title_lower]

