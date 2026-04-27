import os
import asyncio
import traceback
import discord
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
APPLICATION_CHANNEL_ID = int(os.getenv("APPLICATION_CHANNEL_ID"))

if not TOKEN:
    raise ValueError("TOKEN missing")

# ---------------- BOT ----------------
intents = discord.Intents.default()
intents.message_content = True
intents.members = True

bot = commands.Bot(command_prefix="!", intents=intents)

# ======================================================
# 🔘 APPLY PANEL
# ======================================================

class ApplyModal(discord.ui.Modal, title="SMP Application"):

    nickname = discord.ui.TextInput(label="Minecraft Nick")
    age = discord.ui.TextInput(label="Age")
    source = discord.ui.TextInput(label="How did you find us?")
    friend = discord.ui.TextInput(label="Friend (optional)", required=False)
    about = discord.ui.TextInput(label="About you", style=discord.TextStyle.paragraph)

    async def on_submit(self, interaction: discord.Interaction):
        channel = bot.get_channel(APPLICATION_CHANNEL_ID)

        embed = discord.Embed(
            title="📩 New Application",
            color=0x00ff00
        )

        embed.add_field(name="Nick", value=self.nickname.value, inline=False)
        embed.add_field(name="Age", value=self.age.value, inline=False)
        embed.add_field(name="Source", value=self.source.value, inline=False)
        embed.add_field(name="Friend", value=self.friend.value or "None", inline=False)
        embed.add_field(name="About", value=self.about.value, inline=False)

        await channel.send(embed=embed)

        await interaction.response.send_message(
            "✅ Sent!",
            ephemeral=True
        )


class ApplyView(discord.ui.View):
    def __init__(self):
        super().__init__(timeout=None)

    @discord.ui.button(label="📩 Apply", style=discord.ButtonStyle.green)
    async def apply(self, interaction: discord.Interaction, button: discord.ui.Button):
        await interaction.response.send_modal(ApplyModal())

# ======================================================
# EVENTS
# ======================================================

@bot.event
async def on_ready():
    print(f"✅ Logged in as {bot.user}")

    try:
        await bot.tree.sync()
        print("🔁 Slash commands synced")
    except Exception as e:
        print("Sync error:", e)

    bot.loop.create_task(mc_loop())


@bot.event
async def on_message(message):
    try:
        if message.author.bot:
            return

        await discord_to_mc(message)

        await bot.process_commands(message)

    except Exception:
        traceback.print_exc()

# ======================================================
# MC LOOP (SAFE - NO SPAM CONTROL HERE)
# ======================================================

async def mc_loop():
    await bot.wait_until_ready()

    print("MC LOOP STARTED")

    while not bot.is_closed():
        try:
            await minecraft_to_discord(bot, CHANNEL_ID)

        except Exception:
            traceback.print_exc()

        await asyncio.sleep(5)

# ======================================================
# SLASH COMMANDS
# ======================================================

@bot.tree.command(name="apply", description="Apply to SMP")
async def apply(interaction: discord.Interaction, nickname: str, reason: str):
    try:
        create_application(interaction.user.id, nickname, reason)
        await interaction.response.send_message("🧾 Saved", ephemeral=True)
    except:
        traceback.print_exc()


@bot.tree.command(name="report", description="Report player")
async def report(interaction: discord.Interaction, target: str, reason: str):
    try:
        create_report(interaction.user.name, target, reason)
        await interaction.response.send_message("🚨 Sent", ephemeral=True)
    except:
        traceback.print_exc()


@bot.tree.command(name="verify", description="Link MC account")
async def verify(interaction: discord.Interaction, mc_name: str):
    try:
        code = await start_verification(interaction.user.id, mc_name)
        await interaction.response.send_message(f"🔐 Code: {code}", ephemeral=True)
    except:
        traceback.print_exc()

# ======================================================
# ADMIN PANEL
# ======================================================

@bot.tree.command(name="setup_apply_panel", description="Create apply panel")
async def setup_apply_panel(interaction: discord.Interaction):

    if not interaction.user.guild_permissions.administrator:
        await interaction.response.send_message("No permission", ephemeral=True)
        return

    embed = discord.Embed(
        title="🎮 SMP Applications",
        description="Click button below to apply",
        color=0x3498db
    )

    await interaction.channel.send(embed=embed, view=ApplyView())

    await interaction.response.send_message("Panel created", ephemeral=True)

# ======================================================
# RUN
# ======================================================

bot.run(TOKEN)
