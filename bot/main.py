import discord
import asyncio
from discord.ext import commands

from safe_loop import safe_task
from chat_bridge import discord_to_mc, minecraft_to_discord

intents = discord.Intents.all()
bot = commands.Bot(command_prefix="!", intents=intents)
