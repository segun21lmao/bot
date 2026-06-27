import json
import time
from pathlib import Path
import aiohttp
import asyncio

_BLOCK_MAP = None
_IMAGE_CACHE = {}  # кеш для URL

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
    """Возвращает английское имя блока из ru_blocks.json (или 'stone')"""
    if not title:
        return "stone"
    block_map = _load_block_map()
    title_lower = title.lower().strip()
    if title_lower in block_map:
        return block_map[title_lower]
    return "stone"

async def get_item_image_url_async(item_name: str) -> str:
    """
    Получает URL объёмного рендера блока через API Minecraft Wiki.
    Результат кешируется в _IMAGE_CACHE.
    """
    # Если уже есть в кеше, возвращаем
    if item_name in _IMAGE_CACHE:
        return _IMAGE_CACHE[item_name]

    # Преобразуем имя в формат для вики: первая буква заглавная,
    # подчёркивания заменяем пробелами (например, oak_planks -> Oak Planks)
    # Но для многих блоков подходит просто заглавная буква.
    wiki_title = item_name.replace('_', ' ').title()
    # Исключение: если блок называется "stone", то "Stone" — верно.

    url = "https://minecraft.wiki/api.php"
    params = {
        "action": "query",
        "titles": wiki_title,
        "prop": "pageimages",
        "format": "json",
        "pithumbsize": 300,  # можно увеличить до 500 для лучшего качества
    }

    try:
        async with aiohttp.ClientSession() as session:
            async with session.get(url, params=params) as resp:
                data = await resp.json()
                pages = data.get("query", {}).get("pages", {})
                for page_id, page_info in pages.items():
                    if "thumbnail" in page_info:
                        thumb_url = page_info["thumbnail"]["source"]
                        _IMAGE_CACHE[item_name] = thumb_url
                        return thumb_url
    except Exception as e:
        print(f"Ошибка при запросе к вики: {e}")

    # Если не удалось получить через вики, используем старый CDN как fallback
    fallback_url = f"https://cdn.jsdelivr.net/npm/minecraft-assets@latest/assets/minecraft/textures/block/{item_name}.png?t={int(time.time())}"
    _IMAGE_CACHE[item_name] = fallback_url
    return fallback_url

# Старая синхронная функция оставляем для совместимости, но лучше её не использовать
def get_item_image_url(item_name: str) -> str:
    # fallback на CDN
    return f"https://cdn.jsdelivr.net/npm/minecraft-assets@latest/assets/minecraft/textures/block/{item_name}.png?t={int(time.time())}"