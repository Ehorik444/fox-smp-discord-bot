import discord
from discord.ext import commands
import asyncio

from config import TOKEN
from db import init_db
from applications import ApplyButtonView


# =========================
# INTENTS
# =========================

intents = discord.Intents.default()
intents.guilds = True
intents.members = True


# =========================
# BOT CLASS
# =========================

class Bot(commands.Bot):
    def __init__(self):
        super().__init__(
            command_prefix="!",
            intents=intents
        )

    # =========================
    # STARTUP HOOK (FIXED)
    # =========================
    async def setup_hook(self):
        print("🔧 Initializing bot...")

        # 1. DB init
        await init_db()

        # 2. Load extensions safely
        try:
            await self.load_extension("applications")
            print("✅ applications loaded")
        except Exception as e:
            print(f"❌ Failed to load applications: {e}")

        # 3. Sync slash commands
        try:
            await self.tree.sync()
            print("✅ slash commands synced")
        except Exception as e:
            print(f"❌ sync error: {e}")

        # 4. CRITICAL: persistent views (FIX FOR BUTTONS AFTER RESTART)
        self.add_view(ApplyButtonView())
        print("✅ persistent views registered")

    # =========================
    # READY EVENT
    # =========================
    async def on_ready(self):
        print(f"🚀 Logged in as {self.user} (ID: {self.user.id})")
        print("✅ Bot is fully online and stable")


# =========================
# START BOT
# =========================

bot = Bot()

try:
    bot.run(TOKEN)
except Exception as e:
    print(f"❌ Fatal error: {e}")
