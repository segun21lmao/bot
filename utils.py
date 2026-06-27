import json
import aiohttp
import io


with open('ru_blocks.json', 'r', encoding='utf-8') as file:
    blocks_dict = json.load(file)

def get_block_name(name: str) -> str | None:
    # Приводим к нижнему регистру, можно добавить нормализацию через pymorphy2
    return blocks_dict.get(name.lower())



async def fetch_image(session, name: str):
    """Скачивает изображение по URL и возвращает BytesIO"""
    url = f"https://craft-api.vercel.app/images/items/{get_block_name(name)}.png"
    try:
        async with session.get(url) as resp:
            if resp.status == 200:
                return io.BytesIO(await resp.read())
    except:
        pass
    return None