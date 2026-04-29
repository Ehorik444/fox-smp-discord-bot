import discord
from discord.ext import commands
import os
from dotenv import load_dotenv
from db import db

load_dotenv()

TOKEN = os.getenv("TOKEN")


intents = discord.Intents.default()
intents.members = True

bot = commands.Bot(command_prefix="!", intents=intents)


async def load_extensions():
    await bot.load_extension("applications")


@bot.event
async def setup_hook():
    await db.connect()
    await db.init()
    await load_extensions()


@bot.event
async def on_ready():
    print(f"Logged in as {bot.user}")


bot.run(TOKEN)
