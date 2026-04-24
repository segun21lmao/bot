import discord
from discord.ext import commands
from discord import app_commands
from views import FormHolderView
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
        await channel.purge()
        view=FormHolderView()
        embed = discord.Embed(
            title=f"🐙 **Набор в город**", 
            description="Понравился город? Подай зявку!", color=0x00ff00)
        await channel.send(view=view,embed=embed)
        




    
   


# Функция setup для загрузки кога
async def setup(bot: commands.Bot):
    await bot.add_cog(FormManager(bot))

