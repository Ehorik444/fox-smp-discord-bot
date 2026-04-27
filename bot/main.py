import os
import asyncio
import traceback
import discord
from discord.ext import commands
from dotenv import load_dotenv

from chat_bridge import discord_to_mc, minecraft_to_discord

# ---------- LOAD ENV ----------
load_dotenv()

TOKEN = os.getenv("TOKEN")
DISCORD_CHANNEL_ID = os.getenv("DISCORD_CHANNEL_ID")

if not TOKEN:
    raise ValueError("TOKEN is not set in .env")

if not DISCORD_CHANNEL_ID:
    raise ValueError("DISCORD_CHANNEL_ID is not set in .env")

DISCORD_CHANNEL_ID = int(DISCORD_CHANNEL_ID)

# ---------- BOT ----------
intents = discord.Intents.all()
bot = commands.Bot(command_prefix="!", intents=intents)


# ---------- DISCORD -> MINECRAFT ----------
@bot.event
async def on_message(message):
    try:
        if message.author.bot:
            return

        await discord_to_mc(message)

        await bot.process_commands(message)

    except Exception as e:
        print("on_message error:")
        traceback.print_exc()


# ---------- MINECRAFT -> DISCORD LOOP ----------
async def mc_loop():
    await bot.wait_until_ready()

    channel = None

    while channel is None:
        channel = bot.get_channel(DISCORD_CHANNEL_ID)
        await asyncio.sleep(1)

    print("MC LOOP STARTED")

    while not bot.is_closed():
        try:
            await minecraft_to_discord(bot)

        except Exception as e:
            print("MC LOOP ERROR:")
            traceback.print_exc()

        await asyncio.sleep(5)


# ---------- ON READY ----------
@bot.event
async def on_ready():
    print(f"BOT STARTED AS: {bot.user}")

    bot.loop.create_task(mc_loop())


# ---------- GLOBAL ERROR HANDLER ----------
def handle_exception(loop, context):
    print("GLOBAL ERROR:")
    print(context)


asyncio.get_event_loop().set_exception_handler(handle_exception)


# ---------- RUN ----------
bot.run(TOKEN)
