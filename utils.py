import json
from pathlib import Path

_BLOCK_MAP = None

def _load_block_map():
    global _BLOCK_MAP
    if _BLOCK_MAP is not None:
        return _BLOCK_MAP
    json_path = Path(__file__).parent / "ru_blocks.json"
    try:
        with open(json_path, "r", encoding="utf-8") as f:
            data = json.load(f)
        _BLOCK_MAP = {key.lower(): value for key, value in data.items()}
    except:
        _BLOCK_MAP = {}
    return _BLOCK_MAP

def get_block_name(title: str) -> str:
    if not title:
        return "stone"
    block_map = _load_block_map()
    title_lower = title.lower().strip()
    if title_lower in block_map:
        return block_map[title_lower]
    return "stone"

def get_item_image_url(item_name: str) -> str:
    # Используем raw.githubusercontent.com с фиксированной версией
    return f"https://raw.githubusercontent.com/InventivetalentDev/minecraft-assets/1.21/assets/minecraft/textures/block/{item_name}.png"