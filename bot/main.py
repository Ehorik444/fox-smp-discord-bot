import discord
from discord.ext import commands
import asyncio
import os
import traceback

from config import TOKEN, GUILD_ID
from db import init_db
from applications import ApplyButtonView


# =========================
# INTENTS (STABLE)
# =========================

intents = discord.Intents.default()
intents.guilds = True
intents.members = True
intents.message_content = False  # slash-only бот


# =========================
# BOT CORE
# =========================

class StableBot(commands.Bot):
    def __init__(self):
        super().__init__(
            command_prefix="!",
            intents=intents,
            help_command=None
        )

        self._synced = False  # защита от rate-limit sync

    # =========================
    # SETUP HOOK (SAFE)
    # =========================
    async def setup_hook(self):
        print("⚙️ setup_hook started")

        try:
            await init_db()
            print("✅ DB ready")

            # extensions load safe
            await self.load_extensions_safe()

            # views (persistent buttons)
            self.add_view(ApplyButtonView())
            print("✅ persistent views loaded")

            # slash sync ONLY ONCE
            await self.safe_sync_commands()

        except Exception as e:
            print("❌ setup_hook error:")
            traceback.print_exc()

    # =========================
    # SAFE EXTENSIONS
    # =========================
    async def load_extensions_safe(self):
        extensions = ["applications"]

        for ext in extensions:
            try:
                await self.load_extension(ext)
                print(f"✅ loaded: {ext}")
            except Exception:
                print(f"❌ failed extension: {ext}")
                traceback.print_exc()

    # =========================
    # SAFE SYNC (ANTI RATE LIMIT)
    # =========================
    async def safe_sync_commands(self):
        if self._synced:
            print("⚠️ sync skipped (already synced)")
            return

        try:
            # 🔥 GUILD SYNC = NO RATE LIMIT
            guild = discord.Object(id=GUILD_ID)

            await self.tree.sync(guild=guild)

            self._synced = True
            print("✅ slash commands synced (guild)")

        except Exception:
            print("❌ sync error")
            traceback.print_exc()

    # =========================
    # READY EVENT
    # =========================
    async def on_ready(self):
        print(f"🚀 Logged in as {self.user}")
        print(f"📡 Guilds: {len(self.guilds)}")
        print("🟢 BOT IS STABLE AND ONLINE")


# =========================
# GLOBAL ERROR HANDLER
# =========================

async def handle_global_error(loop, context):
    print("🔥 GLOBAL ERROR:")
    print(context.get("exception"))


# =========================
# START BOT
# =========================

def run_bot():
    bot = StableBot()

    loop = asyncio.new_event_loop()
    asyncio.set_event_loop(loop)
    loop.set_exception_handler(handle_global_error)

    try:
        bot.run(TOKEN)
    except Exception:
        print("💥 FATAL CRASH:")
        traceback.print_exc()


if __name__ == "__main__":
    run_bot()
