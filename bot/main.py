import discord
from discord.ext import commands
import os

TOKEN = os.getenv("TOKEN")

intents = discord.Intents.default()
intents.message_content = True
intents.members = True

bot = commands.Bot(command_prefix="!", intents=intents)


# =========================
# AUTO-DEFER (🔥 главное)
# =========================

@bot.tree.interaction_check
async def auto_defer(interaction: discord.Interaction):
    try:
        if not interaction.response.is_done():
            await interaction.response.defer()
    except:
        pass
    return True


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
    print(f"✅ Бот онлайн: {bot.user}")

    try:
        synced = await bot.tree.sync()
        print(f"🔁 Синхронизировано команд: {len(synced)}")
    except Exception as e:
        print("Sync error:", e)


# =========================
# SETUP HOOK
# =========================

@bot.setup_hook
async def setup_hook():
    await load_extensions()


# =========================
# ERROR HANDLER
# =========================

@bot.event
async def on_error(event, *args, **kwargs):
    print(f"🔥 Ошибка: {event}", args, kwargs)


@bot.tree.error
async def on_app_command_error(interaction, error):
    print("SLASH ERROR:", error)

    try:
        if interaction.response.is_done():
            await interaction.followup.send("❌ Ошибка при выполнении команды", ephemeral=True)
        else:
            await interaction.response.send_message("❌ Ошибка при выполнении команды", ephemeral=True)
    except:
        pass


# =========================
# RUN
# =========================

bot.run(TOKEN)
