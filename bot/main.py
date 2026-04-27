import discord
import asyncio
import traceback
from discord.ext import commands

from chat_bridge import discord_to_mc, minecraft_to_discord

intents = discord.Intents.all()
bot = commands.Bot(command_prefix="!", intents=intents)


# 💬 Discord → MC
@bot.event
async def on_message(message):
    try:
        print("MESSAGE:", message.content)

        if message.author.bot:
            return

        await discord_to_mc(message)
        await bot.process_commands(message)

    except Exception as e:
        print("ON_MESSAGE ERROR:")
        traceback.print_exc()


# 🔁 MC LOOP (ЖЁСТКИЙ DEBUG)
async def mc_loop():
    await bot.wait_until_ready()

    print("MC LOOP STARTED")

    while True:
        try:
            print("MC LOOP TICK")

            players = await minecraft_to_discord(bot)

            print("PLAYERS:", players)

        except Exception as e:
            print("MC LOOP ERROR:")
            traceback.print_exc()

        await asyncio.sleep(5)


@bot.event
async def on_ready():
    print("BOT STARTED:", bot.user)

    bot.loop.create_task(mc_loop())


# 💥 ГЛОБАЛЬНАЯ ЛОВУШКА
def handle_exception(loop, context):
    print("GLOBAL ERROR:")
    print(context)

asyncio.get_event_loop().set_exception_handler(handle_exception)


bot.run("YOUR_TOKEN")
