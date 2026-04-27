import os
import asyncio
import traceback
import discord
from discord import app_commands
from discord.ext import commands
from dotenv import load_dotenv

from chat_bridge import discord_to_mc, minecraft_to_discord
from systems.apply import create_application
from systems.report import create_report
from systems.verify import start_verification

# ---------------- ENV ----------------
load_dotenv()

TOKEN = os.getenv("TOKEN")
CHANNEL_ID = int(os.getenv("DISCORD_CHANNEL_ID"))

if not TOKEN:
    raise ValueError("TOKEN missing")

# ---------------- BOT ----------------
intents = discord.Intents.default()
intents.message_content = True
intents.members = True

bot = commands.Bot(command_prefix="!", intents=intents)


# ---------------- SYNC SLASH COMMANDS ----------------
@bot.event
async def on_ready():
    print(f"✅ BOT ONLINE: {bot.user}")

    try:
        synced = await bot.tree.sync()
        print(f"🔁 Slash commands synced: {len(synced)}")
    except Exception as e:
        print("Sync error:", e)

    bot.loop.create_task(mc_loop())


# ---------------- MC LOOP ----------------
async def mc_loop():
    await bot.wait_until_ready()

    while not bot.is_closed():
        try:
            await minecraft_to_discord(bot, CHANNEL_ID)
        except:
            traceback.print_exc()

        await asyncio.sleep(5)


# ---------------- CHAT (Discord -> MC) ----------------
@bot.event
async def on_message(message):
    try:
        if message.author.bot:
            return

        await discord_to_mc(message)
        await bot.process_commands(message)

    except:
        traceback.print_exc()


# ======================================================
# 🧾 SLASH COMMANDS
# ======================================================

# APPLY
@bot.tree.command(name="apply", description="Apply for SMP server")
async def apply(interaction: discord.Interaction, nickname: str, reason: str):
    try:
        create_application(interaction.user.id, nickname, reason)
        await interaction.response.send_message("🧾 Application submitted!", ephemeral=True)
    except:
        traceback.print_exc()
        await interaction.response.send_message("❌ Error", ephemeral=True)


# REPORT
@bot.tree.command(name="report", description="Report a player")
async def report(interaction: discord.Interaction, target: str, reason: str):
    try:
        create_report(interaction.user.name, target, reason)
        await interaction.response.send_message("🚨 Report sent!", ephemeral=True)
    except:
        traceback.print_exc()
        await interaction.response.send_message("❌ Error", ephemeral=True)


# VERIFY
@bot.tree.command(name="verify", description="Link Minecraft account")
async def verify(interaction: discord.Interaction, mc_name: str):
    try:
        code = await start_verification(interaction.user.id, mc_name)
        await interaction.response.send_message(
            f"🔐 Your code was sent in Minecraft: `{code}`",
            ephemeral=True
        )
    except:
        traceback.print_exc()
        await interaction.response.send_message("❌ Error", ephemeral=True)


# ---------------- RUN ----------------
bot.run(TOKEN)
