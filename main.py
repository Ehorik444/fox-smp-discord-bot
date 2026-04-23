import os
import io
import discord
import aiohttp
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt

from discord import app_commands
from dotenv import load_dotenv

load_dotenv()

TOKEN = os.getenv("DISCORD_TOKEN")

API_URL = os.getenv("API_URL", "http://localhost:8000")

intents = discord.Intents.default()
intents.members = True

bot = discord.Client(intents=intents)
tree = app_commands.CommandTree(bot)

http: aiohttp.ClientSession = None


# ================= HTTP LAYER (FAST + SHARED) =================
async def api_get(path: str):
    async with http.get(f"{API_URL}{path}") as r:
        if r.status != 200:
            return None
        return await r.json()


# ================= PROFILE =================
@tree.command(name="profile")
async def profile(interaction: discord.Interaction):

    data = await api_get(f"/profile/{interaction.user.id}")

    if not data:
        await interaction.response.send_message("❌ Нет данных", ephemeral=True)
        return

    # graph from API
    stats = data.get("activity", [])

    fig, ax = plt.subplots()
    ax.plot([x["date"] for x in stats], [x["value"] for x in stats])

    buf = io.BytesIO()
    fig.savefig(buf, format="png")
    buf.seek(0)
    plt.close(fig)

    embed = discord.Embed(title="Profile")
    embed.add_field(name="Nick", value=data["nick"])
    embed.add_field(name="Hours", value=data["hours"])
    embed.add_field(name="Level", value=data["level"])

    await interaction.response.send_message(
        embed=embed,
        file=discord.File(buf, "graph.png")
    )


# ================= PVP TOP (ZERO COMPUTE BOT SIDE) =================
@tree.command(name="pvp_top")
async def pvp_top(interaction: discord.Interaction):

    data = await api_get("/pvp/top")

    if not data:
        await interaction.response.send_message("❌ API error", ephemeral=True)
        return

    text = "\n".join(
        f"{i+1}. {p['name']} - {p['rating']}"
        for i, p in enumerate(data)
    )

    embed = discord.Embed(title="PvP Top", description=text)

    await interaction.response.send_message(embed=embed)


# ================= APPLICATION =================
class ApplicationModal(discord.ui.Modal, title="Заявка"):

    nickname = discord.ui.TextInput(label="Minecraft ник")
    age = discord.ui.TextInput(label="Возраст")
    about = discord.ui.TextInput(label="О себе", style=discord.TextStyle.paragraph)

    async def on_submit(self, interaction: discord.Interaction):

        payload = {
            "user_id": interaction.user.id,
            "nickname": self.nickname.value,
            "age": int(self.age.value),
            "about": self.about.value
        }

        result = await api_get("/application/submit")

        if not result:
            await interaction.response.send_message("❌ error", ephemeral=True)
            return

        await interaction.response.send_message("📨 Отправлено", ephemeral=True)


# ================= READY =================
@bot.event
async def on_ready():

    global http

    http = aiohttp.ClientSession()

    await tree.sync()

    print("🚀 ENTERPRISE BOT READY")


bot.run(TOKEN)
