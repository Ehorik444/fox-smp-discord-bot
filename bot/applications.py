import discord
from discord.ext import commands
import os

APPLICATION_CHANNEL_ID = int(os.getenv("APPLICATION_CHANNEL_ID", "0"))

# =========================
# MODAL
# =========================

class ApplicationModal(discord.ui.Modal, title="📩 Заявка"):

    nickname = discord.ui.TextInput(label="Ник")
    age = discord.ui.TextInput(label="Возраст")
    source = discord.ui.TextInput(label="Откуда узнал")
    friend = discord.ui.TextInput(label="Ник друга", required=False)
    about = discord.ui.TextInput(label="О себе", style=discord.TextStyle.paragraph)

    async def on_submit(self, interaction: discord.Interaction):

        channel = interaction.guild.get_channel(APPLICATION_CHANNEL_ID)

        embed = discord.Embed(
            title="📩 Новая заявка",
            color=0xfe8b29
        )

        embed.add_field(name="Ник", value=self.nickname.value)
        embed.add_field(name="Возраст", value=self.age.value)
        embed.add_field(name="Источник", value=self.source.value)
        embed.add_field(name="Друг", value=self.friend.value or "Нет")
        embed.add_field(name="О себе", value=self.about.value)

        await channel.send(embed=embed)

        await interaction.response.send_message("✅ Отправлено", ephemeral=True)

# =========================
# VIEW (кнопка создания заявки)
# =========================

class ApplicationView(discord.ui.View):

    @discord.ui.button(label="📩 Подать заявку", style=discord.ButtonStyle.success)
    async def apply(self, interaction: discord.Interaction, button: discord.ui.Button):
        await interaction.response.send_modal(ApplicationModal())

# =========================
# COMMAND
# =========================

class Applications(commands.Cog):
    def __init__(self, bot):
        self.bot = bot

    @commands.hybrid_command(name="заявка")
    async def send_application_panel(self, ctx):

        embed = discord.Embed(
            title="📩 Заявки на сервер",
            description="Нажми кнопку ниже чтобы подать заявку",
            color=0xfe8b29
        )

        await ctx.send(embed=embed, view=ApplicationView())


async def setup(bot):
    await bot.add_cog(Applications(bot))
