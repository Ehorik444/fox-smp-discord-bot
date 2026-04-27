import discord
from discord.ext import commands
import os

TOKEN = os.getenv("TOKEN")

# =========================
# ⚙️ INTENTS
# =========================

intents = discord.Intents.default()
intents.message_content = True
intents.members = True

# =========================
# 🤖 BOT
# =========================

class MyBot(commands.Bot):
    def __init__(self):
        super().__init__(
            command_prefix="!",
            intents=intents
        )

    async def setup_hook(self):
        # 🔥 загружаем все модули
        await self.load_extension("panel")
        await self.load_extension("applications")
        await self.load_extension("link_system")

        # 🔁 синк slash команд
        await self.tree.sync()
        print("🔁 Slash commands synced")

# =========================
# 🚀 START
# =========================

bot = MyBot()

@bot.event
async def on_ready():
    print(f"✅ Бот запущен как {bot.user}")

# =========================
# 🛡️ SAFE RUN
# =========================

try:
    bot.run(TOKEN)
except Exception as e:
    print("CRITICAL ERROR:", e)
