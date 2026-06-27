import json

with open('ru_blocks.json', 'r', encoding='utf-8') as file:
    blocks_dict = json.load(file)

def get_block_name(name: str) -> str | None:
    # Приводим к нижнему регистру, можно добавить нормализацию через pymorphy2
    return blocks_dict.get(name.lower())
