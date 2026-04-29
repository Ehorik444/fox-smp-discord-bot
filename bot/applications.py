import discord
from discord import app_commands
from db import create_application
from utils import check_cooldown, check_daily_limit
from config import APPLICATION_LOG_CHANNEL


# =========================
# VIEW (КНОПКА ПОДАТЬ ЗАЯВКУ)
# =========================

class ApplyButtonView(discord.ui.View):
    def __init__(self):
        super().__init__(timeout=None)

    @discord.ui.button(
        label="📩 Подать заявку",
        style=discord.ButtonStyle.green,
        custom_id="apply_button_main"
    )
    async def apply_button(self, interaction: discord.Interaction, button: discord.ui.Button):
        await interaction.response.send_modal(ApplyModal())


# =========================
# MODAL (форма заявки)
# =========================

class ApplyModal(discord.ui.Modal, title="Заявка"):
    text = discord.ui.TextInput(
        label="Твоя заявка",
        style=discord.TextStyle.paragraph,
        required=True,
        max_length=1000
    )

    async def on_submit(self, interaction: discord.Interaction):

        user_id = interaction.user.id

        if not check_cooldown(user_id):
            return await interaction.response.send_message("⏳ Кулдаун 60 сек", ephemeral=True)

        if not check_daily_limit(user_id):
            return await interaction.response.send_message("🚫 1 заявка в день", ephemeral=True)

        await create_application(user_id, str(self.text))

        channel = interaction.client.get_channel(APPLICATION_LOG_CHANNEL)

        embed = discord.Embed(
            title="📥 Новая заявка",
            description=self.text,
            color=0x2ecc71
        )

        await channel.send(embed=embed)

        await interaction.response.send_message("✅ Заявка отправлена", ephemeral=True)


# =========================
# SLASH COMMAND GROUP
# =========================

class ApplyPanel(app_commands.Group):

    def __init__(self):
        super().__init__(name="apply", description="Система заявок")

    @app_commands.command(name="panel", description="Создать панель заявок")
    async def panel(self, interaction: discord.Interaction):

        embed = discord.Embed(
            title="📌 Заявки",
            description="Нажми кнопку ниже, чтобы подать заявку",
            color=0x3498db
        )

        await interaction.channel.send(
            embed=embed,
            view=ApplyButtonView()
        )

        await interaction.response.send_message("✅ Панель создана", ephemeral=True)


# =========================
# SETUP EXTENSION
# =========================

async def setup(bot):
    bot.tree.add_command(ApplyPanel())

    # 🔥 важно: регистрация persistent view
    bot.add_view(ApplyButtonView())
