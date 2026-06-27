import json
import time
from pathlib import Path
import aiohttp
from bs4 import BeautifulSoup

_BLOCK_MAP = None
_IMAGE_CACHE = {}

# Суффиксы цветных блоков (после цвета идёт именно этот суффикс)
COLORED_SUFFIXES = [
    "_wool", "_stained_glass", "_carpet", "_concrete", "_concrete_powder",
    "_glazed_terracotta", "_terracotta", "_banner", "_bed", "_candle",
    "_shulker_box", "_dye"
]

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

def _is_colored_block(eng_name: str) -> bool:
    for suffix in COLORED_SUFFIXES:
        if eng_name.endswith(suffix):
            return True
    return False

def _generate_colored_url(eng_name: str) -> str:
    for suffix in COLORED_SUFFIXES:
        if eng_name.endswith(suffix):
            base = eng_name[:-len(suffix)]
            color_part = base.replace('_', ' ').title().replace(' ', '_')
            type_part = suffix[1:].replace('_', ' ').title().replace(' ', '_')
            return f"https://minecraft.wiki/images/{color_part}_{type_part}_JE3_BE3.png"
    return None

async def get_item_image_url_async(block_name: str) -> str:
    if block_name in _IMAGE_CACHE:
        return _IMAGE_CACHE[block_name]

    image_url = None

    # 1. Если цветной блок – генерируем URL
    if _is_colored_block(block_name):
        image_url = _generate_colored_url(block_name)
        # Проверяем существование файла (HEAD-запрос)
        if image_url:
            async with aiohttp.ClientSession() as session:
                try:
                    async with session.head(image_url, timeout=5) as resp:
                        if resp.status != 200:
                            # Пробуем JE4_BE4
                            alt_url = image_url.replace("JE3_BE3", "JE4_BE4")
                            async with session.head(alt_url, timeout=5) as resp2:
                                if resp2.status == 200:
                                    image_url = alt_url
                                else:
                                    # Пробуем без суффикса
                                    alt_url2 = image_url.replace("_JE3_BE3", "")
                                    async with session.head(alt_url2, timeout=5) as resp3:
                                        if resp3.status == 200:
                                            image_url = alt_url2
                except Exception as e:
                    print(f"[HEAD error] {e}")

    # 2. Если не цветной или не удалось получить – парсим страницу
    if not image_url:
        page_title = block_name.replace('_', ' ').title().replace(' ', '_')
        wiki_url = f"https://minecraft.wiki/{page_title}"
        async with aiohttp.ClientSession() as session:
            try:
                async with session.get(wiki_url, timeout=10) as resp:
                    if resp.status == 200:
                        html = await resp.text()
                        soup = BeautifulSoup(html, 'html.parser')
                        meta = soup.find('meta', property='og:image')
                        if meta and meta.get('content'):
                            image_url = meta['content']
            except Exception as e:
                print(f"[Parse error] {e}")

    # 3. Fallback – плоская иконка
    if not image_url:
        image_url = f"https://cdn.jsdelivr.net/npm/minecraft-assets@latest/assets/minecraft/textures/block/{block_name}.png"

    # Добавляем параметр для сброса кеша
    if '?' in image_url:
        image_url += f"&t={int(time.time()*1000)}"
    else:
        image_url += f"?t={int(time.time()*1000)}"

    _IMAGE_CACHE[block_name] = image_url
    return image_url