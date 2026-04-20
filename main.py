import discord
from discord import app_commands
from discord.ext import commands
import config 
from db import init_db
import os
from dotenv import load_dotenv


DISCORD_TOKEN = os.getenv('DISCORD_TOKEN')

intents = discord.Intents.default()
intents.message_content = True 
bot = commands.Bot(command_prefix='!', intents=intents)

async def load_cogs():
    await bot.load_extension("cogs.taskmanager")


@bot.event
async def on_ready():
    print(f"Бот {bot.user} запущен")
    await init_db()          # 1. Создаём таблицы
    await load_cogs()        # 2. Загружаем коги (теперь БД готова)
    try:
        synced = await bot.tree.sync()
        print(f"Синхронизировано {len(synced)} слеш-команд")
    except Exception as e:
        print(e)

@bot.event
async def on_message(message:discord.Message):
    if message.author == bot.user:  # Ignore self
        return
    
    for ch_id in config.THREAD_CHANNELS:
        if ch_id==message.channel.id:
            await message.create_thread(name="Комментарии", auto_archive_duration=1440)


@bot.tree.command(name="ping", description="Проверка пинга")
async def ping(interaction: discord.Interaction):
    await interaction.response.send_message("Понг!")

if __name__ == "__main__":
    bot.run(DISCORD_TOKEN)