import discord
from discord.ext import commands
import os

TOKEN = os.getenv("TOKEN")

intents = discord.Intents.default()
intents.message_content = True
intents.members = True

bot = commands.Bot(command_prefix="!", intents=intents)

# =========================
# LOAD EXTENSIONS (ПРАВИЛЬНО)
# =========================

async def setup_hook():
    await bot.load_extension("panel")
    await bot.load_extension("applications")

    await bot.tree.sync()
    print("🔁 Slash commands synced")

bot.setup_hook = setup_hook

# =========================
# READY
# =========================

@bot.event
async def on_ready():
    print(f"✅ Logged in as {bot.user}")

# =========================
# RUN
# =========================

bot.run(TOKEN)
