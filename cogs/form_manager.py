import discord
from discord.ext import commands
from discord import app_commands
from views import FormHolderView, RoleForm
import asyncio
import config 

class FormManager(commands.Cog):
    def __init__(self, bot: commands.Bot):
        self.bot = bot
        
        

    
    async def cog_load(self):
        await self.restore_persistent_views()
        print("FormManager cog загружен, persistent views восстановлены")

    async def restore_persistent_views(self):
        guild=self.bot.get_guild(config.GUILD)
        channel=guild.get_channel(config.FORM_CHANNEL)
        channel1=guild.get_channel(config.ROLE_CHANNEL)
        await channel.purge()
        await channel1.purge()
        view=FormHolderView()
        embed = discord.Embed(
            title=f"🐙 **Набор в город**", 
            description="Понравился город? Подай зявку!", color=0x00ff00)
        await channel.send(view=view,embed=embed)
        view1=RoleForm()
        embed1 = discord.Embed(
            title=f"🐙 **Выбери роль себе по вкусу!**", 
            description=f"⛏️ - Добыча ресурсов\n🧱 - Перестройщик по схематике\n🐽 - Создание ферм", color=0x00ff00)
        await channel1.send(view=view1,embed=embed1)
        

        




    
   


# Функция setup для загрузки кога
async def setup(bot: commands.Bot):
    await bot.add_cog(FormManager(bot))

