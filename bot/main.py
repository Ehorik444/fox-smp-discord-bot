import discord
from discord.ext import commands
import os

TOKEN = os.getenv("TOKEN")

intents = discord.Intents.default()
intents.message_content = True
intents.members = True

bot = commands.Bot(command_prefix="!", intents=intents)


# =========================
# LOAD EXTENSIONS
# =========================

async def load_extensions():
    await bot.load_extension("panel")
    await bot.load_extension("applications")


# =========================
# READY
# =========================

@bot.event
async def on_ready():
    print(f"✅ Бот онлайн: {bot.user}")

    try:
        await bot.tree.sync()
        print("🔁 Slash команды синхронизированы")
    except Exception as e:
        print("Sync error:", e)


# =========================
# SETUP HOOK (ВАЖНО)
# =========================

async def setup_hook():
    await load_extensions()

bot.setup_hook = setup_hook  # 💥 ВОТ ТУТ ФИКС


# =========================
# ERROR HANDLER
# =========================

@bot.tree.error
async def on_app_command_error(interaction, error):
    print("SLASH ERROR:", error)

    try:
        if interaction.response.is_done():
            await interaction.followup.send("❌ Ошибка команды", ephemeral=True)
        else:
            await interaction.response.send_message("❌ Ошибка команды", ephemeral=True)
    except:
        pass


# =========================
# RUN
# =========================

bot.run(TOKEN)
