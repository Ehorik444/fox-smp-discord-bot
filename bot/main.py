import os
import asyncio
import traceback
import discord
from discord.ext import commands
from dotenv import load_dotenv

from chat_bridge import discord_to_mc, minecraft_to_discord
from systems.apply import create_application
from systems.report import create_report
from systems.verify import start_verification
from utils.interaction_safe import safe_slash

# ---------------- ENV ----------------
load_dotenv()

TOKEN = os.getenv("TOKEN")
CHANNEL_ID = int(os.getenv("DISCORD_CHANNEL_ID"))
APPLICATION_CHANNEL_ID = int(os.getenv("APPLICATION_CHANNEL_ID"))

if not TOKEN:
    raise ValueError("TOKEN missing")

# ---------------- BOT ----------------
intents = discord.Intents.default()
intents.message_content = True
intents.members = True

bot = commands.Bot(command_prefix="!", intents=intents)

# ======================================================
# 🧾 APPLY MODAL
# ======================================================
class ApplyModal(discord.ui.Modal, title="Заявка на сервер"):

    nickname = discord.ui.TextInput(label="Ник в Minecraft")
    age = discord.ui.TextInput(label="Возраст")
    source = discord.ui.TextInput(label="Откуда узнали сервер?")
    friend = discord.ui.TextInput(label="Ник друга (для розыгрышей)", required=False)
    about = discord.ui.TextInput(label="О себе", style=discord.TextStyle.paragraph)

    async def on_submit(self, interaction: discord.Interaction):
        channel = bot.get_channel(APPLICATION_CHANNEL_ID)

        embed = discord.Embed(
            title="📩 Новая заявка на сервер",
            color=0xfe8b29
        )

        embed.add_field(name="Ник", value=self.nickname.value, inline=False)
        embed.add_field(name="Возраст", value=self.age.value, inline=False)
        embed.add_field(name="Источник", value=self.source.value, inline=False)
        embed.add_field(name="Друг", value=self.friend.value or "Не указан", inline=False)
        embed.add_field(name="О себе", value=self.about.value, inline=False)

        embed.set_footer(text=f"Пользователь: {interaction.user}")

        await channel.send(embed=embed)

        await interaction.response.send_message(
            "✅ Ваша заявка отправлена!",
            ephemeral=True
        )

# ======================================================
# 🔘 APPLY BUTTON
# ======================================================
class ApplyView(discord.ui.View):
    def __init__(self):
        super().__init__(timeout=None)

    @discord.ui.button(
        label="📩 Подать заявку",
        style=discord.ButtonStyle.primary,
        emoji="🟠"
    )
    async def apply(self, interaction: discord.Interaction, button: discord.ui.Button):
        await interaction.response.send_modal(ApplyModal())

# ======================================================
# EVENTS
# ======================================================

@bot.event
async def on_ready():
    print(f"✅ Бот запущен: {bot.user}")

    try:
        await bot.tree.sync()
        print("🔁 Slash команды синхронизированы")
    except Exception as e:
        print("Sync error:", e)

    bot.loop.create_task(mc_loop())


@bot.event
async def on_message(message):
    try:
        if message.author.bot:
            return

        await discord_to_mc(message)
        await bot.process_commands(message)

    except Exception:
        traceback.print_exc()

# ======================================================
# MC LOOP (NO SPAM FIXED IN chat_bridge)
# ======================================================
async def mc_loop():
    await bot.wait_until_ready()

    print("MC LOOP STARTED")

    while not bot.is_closed():
        try:
            await minecraft_to_discord(bot, CHANNEL_ID)

        except Exception:
            traceback.print_exc()

        await asyncio.sleep(5)

# ======================================================
# SLASH COMMANDS (ANTI-TIMEOUT SYSTEM)
# ======================================================

@bot.tree.command(name="apply", description="Подать заявку на SMP сервер")
async def apply(interaction: discord.Interaction, nickname: str, reason: str):

    async def logic():
        create_application(interaction.user.id, nickname, reason)
        return "🧾 Ваша заявка отправлена!"

    await safe_slash(interaction, logic)


@bot.tree.command(name="report", description="Пожаловаться на игрока")
async def report(interaction: discord.Interaction, target: str, reason: str):

    async def logic():
        create_report(interaction.user.name, target, reason)
        return "🚨 Жалоба отправлена!"

    await safe_slash(interaction, logic)


@bot.tree.command(name="verify", description="Привязать Minecraft аккаунт")
async def verify(interaction: discord.Interaction, mc_name: str):

    async def logic():
        code = await start_verification(interaction.user.id, mc_name)
        return f"🔐 Код отправлен в Minecraft: {code}"

    await safe_slash(interaction, logic)

# ======================================================
# ADMIN PANEL
# ======================================================

@bot.tree.command(name="панель_заявок", description="Создать панель заявок")
async def panel(interaction: discord.Interaction):

    if not interaction.user.guild_permissions.administrator:
        await interaction.response.send_message("❌ Нет прав", ephemeral=True)
        return

    embed = discord.Embed(
        title="🎮 Заявки на SMP сервер",
        description="Нажмите кнопку ниже, чтобы подать заявку",
        color=0xfe8b29
    )

    await interaction.channel.send(embed=embed, view=ApplyView())

    await interaction.response.send_message("✅ Панель создана", ephemeral=True)

# ======================================================
# RUN
# ======================================================

bot.run(TOKEN)
