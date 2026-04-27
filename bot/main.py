import os
import asyncio
import traceback
import discord
from discord.ext import commands
from dotenv import load_dotenv

from chat_bridge import discord_to_mc, minecraft_to_discord

# SMP SYSTEMS
from systems.apply import create_application
from systems.report import create_report
from systems.verify import start_verification

# ---------------- ENV ----------------
load_dotenv()

TOKEN = os.getenv("TOKEN")
CHANNEL_ID = int(os.getenv("DISCORD_CHANNEL_ID"))

if not TOKEN:
    raise ValueError("TOKEN missing in .env")

# ---------------- BOT ----------------
intents = discord.Intents.all()
bot = commands.Bot(command_prefix="/", intents=intents)


# ---------------- CHAT DISCORD -> MC ----------------
@bot.event
async def on_message(message):
    try:
        if message.author.bot:
            return

        await discord_to_mc(message)
        await bot.process_commands(message)

    except Exception:
        print("on_message ERROR")
        traceback.print_exc()


# ---------------- MC LOOP ----------------
async def mc_loop():
    await bot.wait_until_ready()

    print("MC LOOP STARTED")

    while not bot.is_closed():
        try:
            await minecraft_to_discord(bot, CHANNEL_ID)

        except Exception:
            print("MC LOOP ERROR")
            traceback.print_exc()

        await asyncio.sleep(5)


# ---------------- READY ----------------
@bot.event
async def on_ready():
    print(f"✅ SMP BOT ONLINE: {bot.user}")

    bot.loop.create_task(mc_loop())


# ---------------- COMMANDS ----------------

# 🧾 APPLY
@bot.command()
async def apply(ctx, nickname: str, *, reason: str):
    try:
        create_application(ctx.author.id, nickname, reason)
        await ctx.send("🧾 Application sent!")
    except Exception:
        traceback.print_exc()
        await ctx.send("❌ Error while sending application")


# 🚨 REPORT
@bot.command()
async def report(ctx, target: str, *, reason: str):
    try:
        create_report(ctx.author.name, target, reason)
        await ctx.send("🚨 Report submitted!")
    except Exception:
        traceback.print_exc()
        await ctx.send("❌ Error while reporting")


# 🔐 VERIFY
@bot.command()
async def verify(ctx, mc_name: str):
    try:
        code = await start_verification(ctx.author.id, mc_name)
        await ctx.send(f"🔐 Code sent to Minecraft: `{code}`")
    except Exception:
        traceback.print_exc()
        await ctx.send("❌ Verification error")


# ---------------- GLOBAL ERROR HANDLER ----------------
def handle_exception(loop, context):
    print("GLOBAL ERROR:", context)


asyncio.get_event_loop().set_exception_handler(handle_exception)


# ---------------- RUN ----------------
bot.run(TOKEN)
