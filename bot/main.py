import discord
from discord.ext import commands
import asyncio
import os

TOKEN = os.getenv("TOKEN")

intents = discord.Intents.default()
intents.message_content = True

bot = commands.Bot(command_prefix="!", intents=intents)

EXTENSIONS = ["applications"]

async def load_extensions():
    for ext in EXTENSIONS:
        try:
            await bot.load_extension(ext)
            print(f"✅ Loaded {ext}")
        except Exception as e:
            print(f"❌ Error loading {ext}: {e}")

@bot.event
async def setup_hook():
    await load_extensions()

@bot.event
async def on_ready():
    print(f"Bot online as {bot.user}")

bot.run(TOKEN)
