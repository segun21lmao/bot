import json
import time
from pathlib import Path
import aiohttp
import asyncio

_BLOCK_MAP = None
_IMAGE_CACHE = {}

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
        return "chest"
    block_map = _load_block_map()
    title_lower = title.lower().strip()
    if title_lower in block_map:
        return block_map[title_lower]
    return "chest"

async def get_item_image_url_async(item_name: str) -> str:
    print(f"[DEBUG] Запрос для {item_name}")
    """
    Получает URL объёмного рендера блока.
    1) Пытается взять thumbnail через API вики.
    2) Если нет – ищет изображения на странице и берёт первое подходящее.
    3) Если и это не удалось – возвращает плоскую иконку с CDN.
    """
    if item_name in _IMAGE_CACHE:
        return _IMAGE_CACHE[item_name]

    wiki_title = item_name.replace('_', ' ').title()
    thumb_url = None

    async with aiohttp.ClientSession() as session:
        # Шаг 1: запрос thumbnail
        params = {
            "action": "query",
            "titles": wiki_title,
            "prop": "pageimages",
            "format": "json",
            "pithumbsize": 300,
        }
        try:
            async with session.get("https://minecraft.wiki/api.php", params=params) as resp:
                data = await resp.json()
                pages = data.get("query", {}).get("pages", {})
                for page_id, page_info in pages.items():
                    if "thumbnail" in page_info:
                        thumb_url = page_info["thumbnail"]["source"]
                        break
        except Exception as e:
            print(f"[API thumbnail error] {e}")

        # Шаг 2: если thumbnail не найден – пытаемся взять изображение из списка images
        if not thumb_url:
            try:
                params = {
                    "action": "query",
                    "titles": wiki_title,
                    "prop": "images",
                    "format": "json",
                }
                async with session.get("https://minecraft.wiki/api.php", params=params) as resp:
                    data = await resp.json()
                    pages = data.get("query", {}).get("pages", {})
                    for page_id, page_info in pages.items():
                        images = page_info.get("images", [])
                        # Выбираем первое изображение в формате PNG (или JPG)
                        for img in images:
                            title = img.get("title", "")
                            if title.startswith("File:") and (".png" in title or ".jpg" in title or ".jpeg" in title):
                                filename = title.replace("File:", "").replace(" ", "_")
                                thumb_url = f"https://minecraft.wiki/images/{filename}"
                                break
                        if thumb_url:
                            break
            except Exception as e:
                print(f"[API images error] {e}")

        # Шаг 3: если всё равно нет – fallback на старый CDN
        if not thumb_url:
            thumb_url = f"https://cdn.jsdelivr.net/npm/minecraft-assets@latest/assets/minecraft/textures/block/{item_name}.png?t={int(time.time())}"

        _IMAGE_CACHE[item_name] = thumb_url
        print(f"[DEBUG] Результат: {thumb_url}")
        return thumb_url
    