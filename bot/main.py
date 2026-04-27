import discord
from discord.ext import commands
import os

TOKEN = os.getenv("TOKEN")

intents = discord.Intents.default()
intents.members = True
intents.message_content = True


class Bot(commands.Bot):
    def __init__(self):
        super().__init__(command_prefix="!", intents=intents)

    async def setup_hook(self):
        await self.load_extension("applications")
        await self.load_extension("link_system")
        await self.tree.sync()
        print("✅ Slash synced")


bot = Bot()

@bot.event
async def on_ready():
    print(f"🤖 Logged in as {bot.user}")


bot.run(TOKEN)
