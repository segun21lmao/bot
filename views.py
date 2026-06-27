import discord
from db import get_task_by_message, add_member, get_task_members, set_task_thread, remove_member, complete_task, get_message_by_task, set_thread_message 
import config 
from discord.ui import View, button, Modal, TextInput
from utils import get_block_name, get_item_image_url_async
import asyncio

async def get_mentions(interaction: discord.Interaction, members: list = None):
    mentions = []
    if members is None:
        members = []
    for uid in members:
        try:
            user = await interaction.guild.fetch_member(uid)
            mentions.append(user.mention)
        except discord.NotFound:
            mentions.append(f"<@{uid}>")
    return mentions

class AcceptTaskView(View):
    def __init__(self, task_id: int, message_id: int):
        super().__init__(timeout=None)
        self.task_id = task_id
        self.message_id = message_id

    async def update_original_message(self, interaction: discord.Interaction):
        members = await get_task_members(self.task_id)
        task = await get_task_by_message(self.message_id)
        image_str = get_block_name(task['title'])
        image_url = await get_item_image_url_async(image_str)
        mentions = await get_mentions(interaction, members)
        extra = ""
        if mentions:
            extra = "\n\n**Принявшие:** " + ", ".join(mentions)
        task_embed = discord.Embed(
            title=f"**Задача:** {task['title']}\n",
            description=f"**Описание:** {task['description']}{extra}",
            color=0xFF9900
        )
        task_embed.set_image(url=image_url)
        await interaction.message.edit(embed=task_embed)

    @button(label="Принять", style=discord.ButtonStyle.primary, custom_id="accept_task")
    async def accept_button(self, interaction: discord.Interaction, button: discord.ui.Button):
        await interaction.response.defer()
        members = await get_task_members(self.task_id)
        if interaction.user.id in members:
            return await interaction.followup.send("Вы уже приняли эту задачу.", ephemeral=True)
        await add_member(self.task_id, interaction.user.id)
        await self.update_original_message(interaction)
        task = await get_task_by_message(self.message_id)
        if task["thread_id"] is None:
            thread = await interaction.message.create_thread(name=f"задача-{interaction.user.name}", auto_archive_duration=1440)
            await set_task_thread(self.task_id, thread.id)
            embed = discord.Embed(title=task["title"], description=task["description"], color=0x00ff00)
            view = TaskControlView(self.task_id, thread.id)
            msg = await thread.send(embed=embed, view=view)
            await set_thread_message(self.task_id, msg.id)
            interaction.client.add_view(view, message_id=msg.id)
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
        task = await get_task_by_message(orig_message_id)  # добавлен await
        mentions = await get_mentions(interaction, members)
        image_str = get_block_name(task['title'])
        image_url = await get_item_image_url_async(image_str)
        extra = "\n\n**Принявшие:** " + ", ".join(mentions) if mentions else ""
        role = interaction.guild.get_role(config.RES_ROLE)
        task_embed = discord.Embed(
            title=f"\n**Задача:** {task['title']}\n",
            description=f"**Описание:** {task['description']}{extra}",
            color=0xFF9900
        )
        task_embed.set_image(url=image_url)
        await orig_message.edit(content=role.mention, embed=task_embed)
        await interaction.followup.send("Вы отказались от задачи.", ephemeral=True)

    @button(label="Выполнено", style=discord.ButtonStyle.success, custom_id="complete_task")
    async def complete_button(self, interaction: discord.Interaction, button: discord.ui.Button):
        await interaction.response.defer()
        thread = interaction.guild.get_thread(self.thread_id)
        if thread is None:
            await interaction.followup.send("❌ Ветка не найдена.", ephemeral=True)
            return
        members = await get_task_members(self.task_id)
        await complete_task(self.task_id)
        orig_message = await thread.parent.fetch_message(await get_message_by_task(self.task_id))
        mentions = await get_mentions(interaction, members)
        task = await get_task_by_message(await get_message_by_task(self.task_id))
        extra = ""
        if mentions:
            extra = "\n\n**Выполнили:** " + ", ".join(mentions)
        # Добавим картинку и в выполненную задачу (опционально)
        image_str = get_block_name(task['title'])
        image_url = await get_item_image_url_async(image_str)
        task_embed = discord.Embed(
            title=f"**Задача:** {task['title']}\n",
            description=f"**Описание:** {task['description']}{extra}",
            color=0x00ff00
        )
        task_embed.set_image(url=image_url)
        await orig_message.edit(embed=task_embed, view=None)
        if thread:
            await interaction.message.edit(content="Задача выполнена!", view=None)
            await thread.edit(locked=True, archived=True)

class FormHolderView(View):
    def __init__(self):
        super().__init__(timeout=None)

    @button(label="Вступить", style=discord.ButtonStyle.primary, custom_id="join")
    async def button_callback(self, interaction: discord.Interaction, button: discord.ui.Button):
        modal = Form(interaction.channel_id)
        await interaction.response.send_modal(modal)

class FormAccept(View):
    def __init__(self, user_id: int):
        super().__init__(timeout=None)
        self.user_id = user_id

    async def is_admin(self, interaction: discord.Interaction) -> bool:
        admin_role_ids = set(config.ADMIN_ROLE)
        return any(role.id in admin_role_ids for role in interaction.user.roles)

    @button(label="Принять", style=discord.ButtonStyle.success, custom_id="accept_form")
    async def accept_button(self, interaction: discord.Interaction, button: discord.ui.Button):
        if not await self.is_admin(interaction):
            await interaction.response.send_message("Не балуйся, эта кнопка не для тебя", ephemeral=True)
            return
        user = await interaction.guild.fetch_member(self.user_id)
        await user.add_roles(interaction.guild.get_role(config.BASE_ROLE))
        await interaction.channel.delete(reason="Заявка принята")

    @button(label="Отклонить", style=discord.ButtonStyle.danger, custom_id="decline_form")
    async def decline_button(self, interaction: discord.Interaction, button: discord.ui.Button):
        if not await self.is_admin(interaction):
            await interaction.response.send_message("Не балуйся, эта кнопка не для тебя", ephemeral=True)
            return
        await interaction.response.send_message("Извините, ваша заявка была отклонена")
        await asyncio.sleep(86400)
        await interaction.channel.delete(reason="Заявка отклонена")

class Form(Modal):
    def __init__(self, channel_id: int):
        super().__init__(title="Заявка")
        self.channel_id = channel_id
        self.add_item(TextInput(
            label="Ваш ник на сервере",
            placeholder="Никнейм",
            style=discord.TextStyle.short,
            required=True
        ))
        self.add_item(TextInput(
            label="Возраст и часовой пояс",
            placeholder="Возраст/часовой пояс",
            style=discord.TextStyle.short,
            required=True
        ))
        self.add_item(TextInput(
            label="Состояли в других городах?",
            placeholder="Да, в .../ Нет",
            style=discord.TextStyle.short,
            required=True
        ))
        self.add_item(TextInput(
            label="Чем хотели бы заниматься в городе?",
            placeholder="Строить, добывать ресурсы, участвовать в ивентах...",
            style=discord.TextStyle.short,
            required=True
        ))
        self.add_item(TextInput(
            label="Кратко расскажите о себе",
            placeholder="Расскажите о себе в нескольких предложениях",
            style=discord.TextStyle.long,
            max_length=300,
            required=True
        ))

    async def on_submit(self, interaction: discord.Interaction):
        await interaction.response.defer()
        channel = interaction.channel
        user = await interaction.guild.fetch_member(interaction.user.id)
        admin = []
        for id in config.ADMIN_ROLE:
            admin.append(interaction.guild.get_role(id))
        thread = await channel.create_thread(name=f"Заявка-{user.name}", type=discord.ChannelType.private_thread, auto_archive_duration=1440)
        await thread.add_user(interaction.user)
        embed_data = {
            "title": f"Заявка-{user.name}",
            "description": (
                f"🪪 Ник на сервере:\n**{self.children[0].value}**\n"
                f"👣 Возраст и часовой пояс:\n**{self.children[1].value}**\n"
                f"🌆 Состояли в других городах?:\n**{self.children[2].value}**\n"
                f"⛏️ Чем хотели бы заниматься в городе?:\n**{self.children[3].value}**\n"
                f"👁️ Расскажите о себе:\n**{self.children[4].value}**"
            ),
            "color": 7256354
        }
        view = FormAccept(interaction.user.id)
        embed = discord.Embed.from_dict(embed_data)
        admin_mention = [adm.mention for adm in admin]
        mentions_str = ', '.join(admin_mention)
        await thread.send(embed=embed, view=view)
        await thread.send(f"{mentions_str} — новая заявка!")

class RoleForm(View):
    def __init__(self):
        super().__init__(timeout=None)

    @button(label="⛏️", style=discord.ButtonStyle.success, custom_id="res_button")
    async def res_button(self, interaction: discord.Interaction, button: discord.ui.Button):
        await interaction.response.defer()
        user = interaction.user
        role = interaction.guild.get_role(1490339118452834365)
        if role not in user.roles:
            await user.add_roles(interaction.guild.get_role(1490339118452834365))
            await interaction.followup.send("Теперь ты ресурсер!", ephemeral=True)
        else:
            await user.remove_roles(interaction.guild.get_role(1490339118452834365))
            await interaction.followup.send("Ты больше не ресурсер", ephemeral=True)

    @button(label="🧱", style=discord.ButtonStyle.success, custom_id="build_button")
    async def build_button(self, interaction: discord.Interaction, button: discord.ui.Button):
        await interaction.response.defer()
        user = interaction.user
        role = interaction.guild.get_role(1490402487490838690)
        if role not in user.roles:
            await user.add_roles(interaction.guild.get_role(1490402487490838690))
            await interaction.followup.send("Теперь ты перестройщик!", ephemeral=True)
        else:
            await user.remove_roles(interaction.guild.get_role(1490402487490838690))
            await interaction.followup.send("Ты больше не перестройщик", ephemeral=True)

    @button(label="🐽", style=discord.ButtonStyle.success, custom_id="farm_button")
    async def farm_button(self, interaction: discord.Interaction, button: discord.ui.Button):
        await interaction.response.defer()
        user = interaction.user
        role = interaction.guild.get_role(1490403240565539006)
        if role not in user.roles:
            await user.add_roles(interaction.guild.get_role(1490403240565539006))
            await interaction.followup.send("Теперь ты редстоунер!", ephemeral=True)
        else:
            await user.remove_roles(interaction.guild.get_role(1490403240565539006))
            await interaction.followup.send("Ты больше не редстоунер", ephemeral=True)