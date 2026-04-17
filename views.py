import discord
from discord.ui import View, button
from db import get_task_by_message, add_member, get_task_members, set_task_thread
import discord
from discord.ui import View, button
from db import get_task_by_message, add_member, get_task_members, set_task_thread, remove_member, complete_task, get_message_by_task
import config 



async def get_mentions(interaction: discord.Interaction, members: list = None):
        mentions = []
        if members is None:
            members = []
        for uid in members:
            try:
                user = await interaction.guild.fetch_member(uid)
                mentions.append(user.mention)
            except discord.NotFound:
                mentions.append(f"<@{uid}>")  # fallback
        return mentions


class AcceptTaskView(View):
    def __init__(self, task_id: int, message_id: int):
        super().__init__(timeout=None)
        self.task_id = task_id
        self.message_id = message_id
    
    

    async def update_original_message(self, interaction: discord.Interaction):
        members = await get_task_members(self.task_id)
        task = await get_task_by_message(self.message_id)
    
        mentions = await get_mentions(interaction, members)
        extra = ""
        if mentions:
            extra = "\n\n**Принявшие:** " + ", ".join(mentions)
        content = f"**Задача:** {task['title']}\n**Описание:** {task['description']}{extra}"
        await interaction.message.edit(content=content)
    

    @button(label="Принять", style=discord.ButtonStyle.primary, custom_id="accept_task")
    async def accept_button(self, interaction: discord.Interaction, button: discord.ui.Button):
        # Отложенный ответ, чтобы не блокировать
        await interaction.response.defer()
        
        # 1. Проверяем, не взял ли уже пользователь
        members = await get_task_members(self.task_id)
        if interaction.user.id in members:
            return await interaction.followup.send("Вы уже приняли эту задачу.", ephemeral=True)

        # 2. Добавляем в БД
        await add_member(self.task_id, interaction.user.id)

        # 3. Обновляем сообщение в канале задач
        await self.update_original_message(interaction)

        # 4. Получаем информацию о задаче
        task = await get_task_by_message(self.message_id)

        # 5. Если ветка задачи ещё не создан — создаём
        if task["thread_id"] is None:
            # Название канала по первому принявшему
            thread = await interaction.message.create_thread(name=f"задача-{interaction.user.name}", auto_archive_duration=1440)
            await set_task_thread(self.task_id, thread.id)
            embed = discord.Embed(title=task["title"], description=task["description"], color=0x00ff00)
            view = TaskControlView(self.task_id, thread.id)
            await thread.send(embed=embed, view=view)
            
        else:
            thread = interaction.guild.get_thread(task["thread_id"])
            if thread:
                 await thread.add_user(interaction.user)

class TaskControlView(View):
    def __init__(self, task_id: int, thread_id: int):
        super().__init__(timeout=None)
        self.task_id = task_id
        self.thread_id = thread_id
        

    @button(label="Отклонить", style=discord.ButtonStyle.danger, custom_id="decline_task")
    async def decline_button(self, interaction: discord.Interaction, button: discord.ui.Button):
        await interaction.response.defer()
        thread = interaction.guild.get_thread(self.thread_id)
        if not thread:
            return await interaction.followup.send("Ветка задачи не найдена.", ephemeral=True)  
        orig_message_id = await get_message_by_task(self.task_id)
        orig_message = await thread.parent.fetch_message(orig_message_id) 
        await remove_member(self.task_id, interaction.user.id)   
        await thread.remove_user(interaction.user)
        members = await get_task_members(self.task_id)
        task = await get_task_by_message(orig_message_id)
        mentions = await get_mentions(interaction, members)
        extra = "\n\n**Принявшие:** " + ", ".join(mentions) if mentions else ""
        role=""
        match task['type']:
                case "res":
                    role=interaction.guild.get_role(config.RES_ROLE)
                case "build":
                    role=interaction.guild.get_role(config.BUILD_ROLE)
        content = f"{role.mention}\n**Задача:** {task['title']}\n**Описание:** {task['description']}{extra}"
        await orig_message.edit(content=content)
    
        await interaction.followup.send("Вы отказались от задачи.", ephemeral=True)
            



        

    @button(label="Выполнено", style=discord.ButtonStyle.success, custom_id="complete_task")
    async def complete_button(self, interaction: discord.Interaction, button: discord.ui.Button):
        await interaction.response.defer()
        thread = interaction.guild.get_thread(self.thread_id)
        members = await get_task_members(self.task_id)
        await complete_task(self.task_id)
        
        orig_message=await thread.parent.fetch_message(await get_message_by_task(self.task_id))
        mentions = await get_mentions(interaction, members)
        task = await get_task_by_message(await get_message_by_task(self.task_id))
        extra = ""
        if mentions:
            extra = "\n\n**Выполнили:** " + ", ".join(mentions)
        content = f"**Задача:** {task['title']}\n**Описание:** {task['description']}{extra}"
    
        
        await orig_message.edit(content=content,view=None)
        if thread:
            await interaction.message.edit(content="задача выполнена!",view=None)
            await thread.edit(locked=True, archived=True)

            
            



    
