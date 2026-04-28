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
# SETUP HOOK
# =========================

@bot.setup_hook
async def setup_hook():
    await load_extensions()


# =========================
# ERROR LOG
# =========================

@bot.event
async def on_error(event, *args, **kwargs):
    print(f"🔥 Ошибка: {event}", args, kwargs)


# =========================
# RUN
# =========================

bot.run(TOKEN)
