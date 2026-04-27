import discord
from discord.ext import commands

class MainPanelView(discord.ui.View):
    def __init__(self):
        super().__init__(timeout=None)

        self.add_item(discord.ui.Button(
            label="💎 Донат",
            style=discord.ButtonStyle.link,
            url="https://buy.fox-smp.ru"
        ))

        self.add_item(discord.ui.Button(
            label="🧱 Сборка",
            style=discord.ButtonStyle.link,
            url="https://modrinth.com/project/foxsmpmodpack"
        ))

        self.add_item(discord.ui.Button(
            label="📱 Telegram",
            style=discord.ButtonStyle.link,
            url="https://t.me/foxsmp_official"
        ))

        self.add_item(discord.ui.Button(
            label="🟦 VK",
            style=discord.ButtonStyle.link,
            url="https://vk.ru/foxsmp_official"
        ))

        self.add_item(discord.ui.Button(
            label="▶️ YouTube",
            style=discord.ButtonStyle.link,
            url="https://youtube.com/@0_ehorik_0.YouTube"
        ))

        self.add_item(discord.ui.Button(
            label="🟣 Twitch",
            style=discord.ButtonStyle.link,
            url="https://m.twitch.tv/0_ehorik_0_/"
        ))

    @discord.ui.button(label="📜 Правила", style=discord.ButtonStyle.primary)
    async def rules(self, interaction: discord.Interaction, button: discord.ui.Button):

        embed = discord.Embed(
            title="📜 Правила FOXSMP",
            description="Правила сервера открываются тут (можем потом расширить на 2 страницы)",
            color=0xfe8b29
        )

        await interaction.response.send_message(embed=embed, ephemeral=True)


class Panel(commands.Cog):
    def __init__(self, bot):
        self.bot = bot

    @commands.hybrid_command(name="панель")
    async def panel(self, ctx: commands.Context):

        embed = discord.Embed(
            title="🎮 FOXSMP PANEL",
            description="Главная панель сервера",
            color=0xfe8b29
        )

        await ctx.send(embed=embed, view=MainPanelView())


async def setup(bot):
    await bot.add_cog(Panel(bot))
