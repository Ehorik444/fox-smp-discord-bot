import discord
from discord.ext import commands
from discord import app_commands


class Panel(commands.Cog):
    def __init__(self, bot):
        self.bot = bot

    @app_commands.command(name="панель", description="Создать панель")
    async def panel(self, interaction: discord.Interaction):

        embed = discord.Embed(
            title="📌 Панель",
            description="Выберите раздел",
            color=0xfe8b29
        )

        view = discord.ui.View()

        view.add_item(discord.ui.Button(label="💎 Донат", url="https://buy.fox-smp.ru"))
        view.add_item(discord.ui.Button(label="📦 Сборка", url="https://modrinth.com/project/foxsmpmodpack"))
        view.add_item(discord.ui.Button(label="📱 VK", url="https://vk.ru/foxsmp_official"))
        view.add_item(discord.ui.Button(label="▶ YouTube", url="https://youtube.com/@0_ehorik_0.YouTube"))
        view.add_item(discord.ui.Button(label="💬 Telegram", url="https://t.me/foxsmp_official"))
        view.add_item(discord.ui.Button(label="🎥 Twitch", url="https://m.twitch.tv/0_ehorik_0_"))

        await interaction.followup.send(embed=embed, view=view)


async def setup(bot):
    await bot.add_cog(Panel(bot))
