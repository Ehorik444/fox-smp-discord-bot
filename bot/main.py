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
    print(f"✅ Logged in as {bot.user}")

    try:
        await load_extensions()
        await bot.tree.sync()
        print("🔁 Slash commands synced")
    except Exception as e:
        print("Error:", e)

# =========================
# RUN
# =========================

bot.run(TOKEN)
