import discord
from discord.ext import commands
import os

# ====== НАСТРОЙКИ ======
APPLICATION_CHANNEL_ID = os.getenv("APPLICATION_CHANNEL_ID")

try:
    APPLICATION_CHANNEL_ID = int(APPLICATION_CHANNEL_ID)
except:
    APPLICATION_CHANNEL_ID = None
    print("⚠️ APPLICATION_CHANNEL_ID не задан")

# ====== МОДАЛКА ======
class ApplyModal(discord.ui.Modal, title="Заявка"):
    name = discord.ui.TextInput(label="Ваше имя", required=True)
    age = discord.ui.TextInput(label="Ваш возраст", required=True)
    reason = discord.ui.TextInput(label="Почему хотите к нам?", style=discord.TextStyle.paragraph)

    async def on_submit(self, interaction: discord.Interaction):
        if APPLICATION_CHANNEL_ID is None:
            await interaction.response.send_message("❌ Канал не настроен", ephemeral=True)
            return

        channel = interaction.client.get_channel(APPLICATION_CHANNEL_ID)

        if channel is None:
            await interaction.response.send_message("❌ Канал не найден", ephemeral=True)
            return

        embed = discord.Embed(
            title="📩 Новая заявка",
            color=discord.Color.green()
        )
        embed.add_field(name="Имя", value=self.name.value, inline=False)
        embed.add_field(name="Возраст", value=self.age.value, inline=False)
        embed.add_field(name="Причина", value=self.reason.value, inline=False)
        embed.set_footer(text=f"От: {interaction.user}")

        await channel.send(embed=embed)

        await interaction.response.send_message("✅ Заявка отправлена!", ephemeral=True)

# ====== КНОПКА ======
class ApplyView(discord.ui.View):
    def __init__(self):
        super().__init__(timeout=None)  # ОБЯЗАТЕЛЬНО для persistent

    @discord.ui.button(label="📨 Подать заявку", style=discord.ButtonStyle.green, custom_id="apply_button")
    async def apply_button(self, interaction: discord.Interaction, button: discord.ui.Button):
        await interaction.response.send_modal(ApplyModal())

# ====== КОМАНДА ======
class Applications(commands.Cog):
    def __init__(self, bot):
        self.bot = bot

    @commands.command()
    async def applypanel(self, ctx):
        """Отправить панель заявок"""
        embed = discord.Embed(
            title="📋 Заявки",
            description="Нажмите кнопку ниже, чтобы подать заявку",
            color=discord.Color.blurple()
        )

        await ctx.send(embed=embed, view=ApplyView())

# ====== ЗАГРУЗКА ======
async def setup(bot):
    await bot.add_cog(Applications(bot))
    bot.add_view(ApplyView())  # важно для persistent
