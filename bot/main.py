import discord
import asyncio
from discord.ext import commands

from chat_bridge import discord_to_mc, minecraft_to_discord
from safe_loop import safe_task

intents = discord.Intents.all()
bot = commands.Bot(command_prefix="!", intents=intents)


# 💬 Discord → Minecraft чат
@bot.event
async def on_message(message):
    try:
        if message.author.bot:
            return

        await discord_to_mc(message)
        await bot.process_commands(message)

    except Exception as e:
        print("on_message error:", e)


# 🔁 Minecraft → Discord loop (СУПЕР СТАБИЛЬНЫЙ)
@safe_task("mc_loop")
async def mc_loop():
    await bot.wait_until_ready()

    while True:
        await minecraft_to_discord(bot)
        await asyncio.sleep(5)


@bot.event
async def on_ready():
    print(f"Bot ready as {bot.user}")

    bot.loop.create_task(mc_loop())


bot.run("YOUR_TOKEN")
