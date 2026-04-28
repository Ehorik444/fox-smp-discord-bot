import discord
from discord.ext import commands
import os
import asyncio

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
    print(f"✅ Бот запущен как {bot.user}")

    try:
        await bot.tree.sync()
        print("🔁 Slash команды синхронизированы")
    except Exception as e:
        print("Sync error:", e)


# =========================
# SETUP HOOK (важно!)
# =========================

@bot.setup_hook
async def setup_hook():
    await load_extensions()


# =========================
# ANTI-CRASH RUN
# =========================

while True:
    try:
        bot.run(TOKEN)
    except Exception as e:
        print("CRASH:", e)
