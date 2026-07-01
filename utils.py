import json
from pathlib import Path
import urllib.parse  

_BLOCK_MAP = None
_IMAGE_CACHE = {}

def _load_block_map():
    global _BLOCK_MAP
    if _BLOCK_MAP is not None:
        return _BLOCK_MAP
    json_path = Path(__file__).parent / "ru_to_link.json"
    try:
        with open(json_path, "r", encoding="utf-8") as f:
            data = json.load(f)
        _BLOCK_MAP = {key.lower(): value for key, value in data.items()}
    except:
        _BLOCK_MAP = {}
    return _BLOCK_MAP

def get_block_name(title: str) -> str:
    if not title:
        # Прямая ссылка на изображение сундука (без /w/File:)
        return "https://minecraft.wiki/images/Chest_(S)_JE1.png"
    
    block_map = _load_block_map()
    title_lower = title.lower().strip()
    url = block_map.get(title_lower, "https://minecraft.wiki/images/Chest_(S)_JE1.png")
    
    # Если ссылка ведёт на страницу вики (содержит "/w/File:"), преобразуем в прямую
    if "/w/File:" in url:
        # Извлекаем имя файла (всё, что после "/w/File:")
        file_name = url.split("/w/File:")[-1]
        # Кодируем спецсимволы (скобки, пробелы и т.п.) для корректного URL
        encoded_name = urllib.parse.quote(file_name)
        # Возвращаем прямую ссылку на изображение
        return f"https://minecraft.wiki/images/{encoded_name}"
    
    # Если ссылка уже прямая (например, начинается с /images/ или содержит .png), оставляем как есть
    return url
