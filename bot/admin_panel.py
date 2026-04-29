import discord
from discord import app_commands
from discord.ext import commands


class AdminPanel(commands.Cog):
    def __init__(self, bot):
        self.bot = bot

    @app_commands.command(name="panel", description="Админ панель")
    async def panel(self, interaction: discord.Interaction):

        if not interaction.user.guild_permissions.administrator:
            return await interaction.response.send_message("Нет прав", ephemeral=True)

        embed = discord.Embed(title="⚙️ Admin Panel")

        await interaction.response.send_message(embed=embed, ephemeral=True)


async def setup(bot):
    await bot.add_cog(AdminPanel(bot))
