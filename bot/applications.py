import discord
from discord import app_commands
from discord.ext import commands
import json
import os
from datetime import datetime, timedelta

# ====== НАСТРОЙКИ ======
APPLICATION_CHANNEL_ID = int(os.getenv("APPLICATION_CHANNEL_ID", "0"))
LOG_CHANNEL_ID = int(os.getenv("LOG_CHANNEL_ID", "0"))

DATA_FILE = "applications_data.json"

# ====== ЗАГРУЗКА ДАННЫХ ======
def load_data():
    if not os.path.exists(DATA_FILE):
        return {}
    with open(DATA_FILE, "r") as f:
        return json.load(f)

def save_data(data):
    with open(DATA_FILE, "w") as f:
        json.dump(data, f, indent=4)

# ====== ПРОВЕРКА ЛИМИТА ======
def can_apply(user_id):
    data = load_data()
    user = data.get(str(user_id))

    if not user:
        return True

    last_time = datetime.fromisoformat(user["last_apply"])
    return datetime.utcnow() - last_time > timedelta(days=1)

def update_apply(user_id):
    data = load_data()
    data[str(user_id)] = {
        "last_apply": datetime.utcnow().isoformat()
    }
    save_data(data)

# ====== VIEW ======
class ApplyView(discord.ui.View):
    def __init__(self):
        super().__init__(timeout=None)

    @discord.ui.button(label="Принять", style=discord.ButtonStyle.green, custom_id="accept_btn")
    async def accept(self, interaction: discord.Interaction, button: discord.ui.Button):
        await interaction.response.send_message("✅ Заявка принята", ephemeral=True)

        log_channel = interaction.client.get_channel(LOG_CHANNEL_ID)
        if log_channel:
            await log_channel.send(f"✅ {interaction.user} принял заявку")

    @discord.ui.button(label="Отказать", style=discord.ButtonStyle.red, custom_id="deny_btn")
    async def deny(self, interaction: discord.Interaction, button: discord.ui.Button):
        await interaction.response.send_message("❌ Заявка отклонена", ephemeral=True)

        log_channel = interaction.client.get_channel(LOG_CHANNEL_ID)
        if log_channel:
            await log_channel.send(f"❌ {interaction.user} отклонил заявку")

# ====== COG ======
class Applications(commands.Cog):
    def __init__(self, bot):
        self.bot = bot

    @app_commands.command(name="apply", description="Подать заявку")
    async def apply(self, interaction: discord.Interaction):
        user_id = interaction.user.id

        # анти-спам (1 раз в день)
        if not can_apply(user_id):
            await interaction.response.send_message(
                "❌ Ты уже отправлял заявку сегодня",
                ephemeral=True
            )
            return

        update_apply(user_id)

        embed = discord.Embed(
            title="📩 Новая заявка",
            description=f"Пользователь: {interaction.user.mention}",
            color=discord.Color.blue()
        )

        channel = self.bot.get_channel(APPLICATION_CHANNEL_ID)
        if not channel:
            await interaction.response.send_message("❌ Канал не найден", ephemeral=True)
            return

        await channel.send(embed=embed, view=ApplyView())

        # лог
        log_channel = self.bot.get_channel(LOG_CHANNEL_ID)
        if log_channel:
            await log_channel.send(f"📨 Новая заявка от {interaction.user}")

        await interaction.response.send_message(
            "✅ Заявка отправлена!",
            ephemeral=True
        )

    @app_commands.command(name="applypanel", description="Создать панель заявок")
    async def applypanel(self, interaction: discord.Interaction):
        embed = discord.Embed(
            title="📋 Заявки",
            description="Нажми кнопку ниже чтобы подать заявку",
            color=discord.Color.green()
        )

        await interaction.channel.send(embed=embed)

        await interaction.response.send_message(
            "✅ Панель создана",
            ephemeral=True
        )

# ====== SETUP ======
async def setup(bot):
    await bot.add_cog(Applications(bot))
    bot.add_view(ApplyView())
