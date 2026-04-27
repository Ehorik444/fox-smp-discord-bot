import os
import asyncio
import traceback
import discord
from discord.ext import commands
from dotenv import load_dotenv

from chat_bridge import discord_to_mc, minecraft_to_discord

load_dotenv()

TOKEN = os.getenv("TOKEN")
CHANNEL_ID = int(os.getenv("DISCORD_CHANNEL_ID"))

intents = discord.Intents.all()
bot = commands.Bot(command_prefix="!", intents=intents)


# 💬 Discord → Minecraft
@bot.event
async def on_message(message):
    try:
        if message.author.bot:
            return

        await discord_to_mc(message)
        await bot.process_commands(message)

    except Exception as e:
        print("on_message ERROR:")
        traceback.print_exc()


# 🔁 Minecraft → Discord LOOP (SAFE)
async def mc_loop():
    await bot.wait_until_ready()

    print("MC LOOP STARTED")

    while True:
        try:
            await minecraft_to_discord(bot, CHANNEL_ID)

        except Exception as e:
            print("MC LOOP ERROR:")
            traceback.print_exc()

        await asyncio.sleep(5)


@bot.event
async def on_ready():
    print("BOT ONLINE:", bot.user)

    bot.loop.create_task(mc_loop())


# 🧠 GLOBAL CRASH PROTECTION
def handle_exception(loop, context):
    print("GLOBAL ERROR:", context)

asyncio.get_event_loop().set_exception_handler(handle_exception)


# 🚀 RUN
bot.run(TOKEN)
