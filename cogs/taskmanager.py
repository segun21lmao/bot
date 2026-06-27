import discord
from discord.ext import commands
from discord import app_commands
from db import create_task, get_task_by_message, get_task_members, add_member, remove_member, complete_task, set_task_thread
from views import AcceptTaskView,TaskControlView
import asyncio
from utils import get_block_name
import config 

class TaskManager(commands.Cog):
    def __init__(self, bot: commands.Bot):
        self.bot = bot

        
        

    
    async def cog_load(self):
        await self.restore_persistent_views()
        print("TaskManager cog загружен, persistent views восстановлены")

    async def restore_persistent_views(self):
        from db import DB_PATH
        import aiosqlite
        async with aiosqlite.connect(DB_PATH) as db:
            async with db.execute("SELECT id, message_id, thread_message_id, thread_id FROM tasks WHERE status = 'active'") as cursor:
                rows = await cursor.fetchall()
                for row in rows:
                    task_id = row[0]
                    msg_id = row[1]
                    tmsg_id=row[2]
                    thr_id=row[3]
                    view = AcceptTaskView(task_id, msg_id)
                    view1 = TaskControlView(task_id,thr_id)
                    # Регистрируем представление в боте, привязывая к ID сообщения
                    self.bot.add_view(view, message_id=msg_id)
                    self.bot.add_view(view1, message_id=tmsg_id)




    @app_commands.command(name="add_task", description="Добавить новую задачу")
    async def add_task(self, interaction: discord.Interaction, title: str, description: str,  count: int = 1):
        channel = interaction.channel  # объект канала
        if not isinstance(channel, discord.TextChannel):
            return await interaction.response.send_message("Команду можно использовать только в текстовом канале.", ephemeral=True)

        await interaction.response.defer(ephemeral=True)
        for i in range(count):
            msg = await channel.send("Загрузка...")
            
            role=interaction.guild.get_role(config.RES_ROLE)
            task_id = await create_task(msg.id, title, description)
            view = AcceptTaskView(task_id, msg.id)
            image_str=get_block_name(title)
            task_embed = discord.Embed(title=f"\n**Задача:** {title}\n", description=f"**Описание:** {description}\n\n**Принявшие:** пока никто", color=0xFF9900)
            if image_str is not None:
                image_url = f"https://cdn.jsdelivr.net/npm/minecraft-assets@1.20.4/assets/minecraft/textures/block/{image_str}.png"
                task_embed.set_image(url=image_url)
            else:
                await interaction.followup.send("Блок не найден,создаю задачу без картинки.", ephemeral=True)
            

                
            await msg.edit(content=role.mention,embed=task_embed, view=view)
            self.bot.add_view(view, message_id=msg.id)
            if count > 1:
                await asyncio.sleep(0.5)  # небольшая задержка между задачами
        


# Функция setup для загрузки кога
async def setup(bot: commands.Bot):
    await bot.add_cog(TaskManager(bot))

