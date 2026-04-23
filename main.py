import os
import asyncio
import discord
import asyncpg
import aiohttp
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
import io
import re

from discord import app_commands
from discord.ui import Modal, TextInput, View
from dotenv import load_dotenv
from mcrcon import MCRcon

load_dotenv()

TOKEN = os.getenv("DISCORD_TOKEN")
DATABASE_URL = os.getenv("DATABASE_URL")

RCON_HOST = os.getenv("RCON_HOST")
RCON_PORT = int(os.getenv("RCON_PORT"))
RCON_PASSWORD = os.getenv("RCON_PASSWORD")

MOD_CHANNEL_ID = int(os.getenv("MOD_CHANNEL_ID"))

LEVEL_1_ROLE = int(os.getenv("LEVEL_1_ROLE"))
LEVEL_2_ROLE = int(os.getenv("LEVEL_2_ROLE"))
LEVEL_3_ROLE = int(os.getenv("LEVEL_3_ROLE"))
LEVEL_4_ROLE = int(os.getenv("LEVEL_4_ROLE"))

intents = discord.Intents.all()
bot = discord.Client(intents=intents)
tree = app_commands.CommandTree(bot)

db: asyncpg.Pool = None


# ================= RCON =================
async def get_playtime(nick: str):
    loop = asyncio.get_running_loop()

    def run():
        with MCRcon(RCON_HOST, RCON_PASSWORD, port=RCON_PORT) as mcr:
            return mcr.command(f"online total {nick}")

    try:
        return await loop.run_in_executor(None, run)
    except:
        return "0 hours"


def parse_hours(text: str):
    h = re.findall(r"(\d+)\s*hour", text)
    m = re.findall(r"(\d+)\s*minute", text)

    hours = sum(map(int, h)) if h else 0
    minutes = sum(map(int, m)) if m else 0

    return hours + minutes // 60


# ================= LEVEL =================
async def update_level(member: discord.Member, hours: int):
    guild = member.guild

    roles = {
        1: guild.get_role(LEVEL_1_ROLE),
        2: guild.get_role(LEVEL_2_ROLE),
        3: guild.get_role(LEVEL_3_ROLE),
        4: guild.get_role(LEVEL_4_ROLE),
    }

    if hours >= 150:
        level = 4
    elif hours >= 50:
        level = 3
    elif hours >= 10:
        level = 2
    else:
        level = 1

    for r in roles.values():
        if r and r in member.roles:
            await member.remove_roles(r)

    if roles[level]:
        await member.add_roles(roles[level])

    return level


# ================= VIEW =================
class ApplicationView(View):
    def __init__(self, user_id: int, nickname: str):
        super().__init__(timeout=None)
        self.user_id = user_id
        self.nickname = nickname

    @discord.ui.button(label="Принять", style=discord.ButtonStyle.green)
    async def accept(self, interaction: discord.Interaction, button: discord.ui.Button):

        async with db.acquire() as conn:
            await conn.execute(
                "UPDATE applications SET status='accepted' WHERE user_id=$1",
                self.user_id
            )

        await interaction.response.send_message("✅ Принято", ephemeral=True)

        # whitelist (optional safety)
        try:
            await whitelist_add(self.nickname)
        except:
            pass

        self.disable_all_items()
        await interaction.message.edit(view=self)


# ================= MODAL =================
class ApplicationModal(Modal, title="Заявка"):
    nickname = TextInput(label="Minecraft ник")
    age = TextInput(label="Возраст")
    about = TextInput(label="О себе", style=discord.TextStyle.paragraph)

    async def on_submit(self, interaction: discord.Interaction):

        user_id = interaction.user.id
        age = int(self.age.value)
        about = self.about.value

        async with db.acquire() as conn:
            row = await conn.fetchrow(
                "SELECT status FROM applications WHERE user_id=$1",
                user_id
            )

            if row and row["status"] == "pending":
                await interaction.response.send_message("❌ Уже есть заявка", ephemeral=True)
                return

            await conn.execute("""
                INSERT INTO applications (user_id, nickname, status)
                VALUES ($1,$2,'pending')
                ON CONFLICT (user_id)
                DO UPDATE SET nickname=$2,status='pending'
            """, user_id, self.nickname.value)

        mod = await bot.fetch_channel(MOD_CHANNEL_ID)

        embed = discord.Embed(title="📨 Заявка")
        embed.add_field(name="Nick", value=self.nickname.value)
        embed.add_field(name="Age", value=str(age))
        embed.add_field(name="About", value=about)

        member = interaction.guild.get_member(user_id)

        # AUTO ACCEPT
        if age >= 14 and len(about) >= 32:

            await update_level(member, 0)

            async with db.acquire() as conn:
                await conn.execute(
                    "UPDATE applications SET status='accepted' WHERE user_id=$1",
                    user_id
                )

            embed.color = 0x00ff00
            embed.add_field(name="Status", value="AUTO ACCEPT")

            await mod.send(embed=embed)
            await interaction.response.send_message("✅ Принят", ephemeral=True)

        else:
            await mod.send(embed=embed, view=ApplicationView(user_id, self.nickname.value))
            await interaction.response.send_message("📨 Отправлено", ephemeral=True)


# ================= PROFILE =================
@tree.command(name="profile")
async def profile(interaction: discord.Interaction):

    async with db.acquire() as conn:
        row = await conn.fetchrow(
            "SELECT nickname FROM applications WHERE user_id=$1",
            interaction.user.id
        )

    if not row:
        await interaction.response.send_message("❌ Нет заявки", ephemeral=True)
        return

    nick = row["nickname"]

    play = await get_playtime(nick)
    hours = parse_hours(play)

    level = await update_level(interaction.user, hours)

    url = f"http://YOUR_SERVER:8804/v1/player/{nick}/activity?period=7"

    async with aiohttp.ClientSession() as s:
        async with s.get(url) as r:
            if r.status != 200:
                await interaction.response.send_message("API error", ephemeral=True)
                return
            data = await r.json()

    days = [d["date"] for d in data]
    vals = [d["activity"] for d in data]

    fig, ax = plt.subplots()
    ax.plot(days, vals)

    buf = io.BytesIO()
    fig.savefig(buf, format="png")
    buf.seek(0)
    plt.close(fig)

    file = discord.File(buf, "graph.png")

    embed = discord.Embed(title="Профиль")
    embed.add_field(name="Nick", value=nick)
    embed.add_field(name="Hours", value=str(hours))
    embed.add_field(name="Level", value=str(level))

    await interaction.response.send_message(embed=embed, file=file)


# ================= PvP TOP =================
@tree.command(name="pvp_top_global")
async def pvp_top_global(interaction: discord.Interaction):

    await interaction.response.defer()

    async with aiohttp.ClientSession() as s:
        async with s.get("http://YOUR_SERVER:8804/v1/players") as r:
            players = await r.json()

    data = []

    for p in players:
        rating = calculate_pvp_rating(p.get("kills", 0), p.get("deaths", 0))
        data.append((p["name"], rating))

    data.sort(key=lambda x: x[1], reverse=True)

    text = "\n".join([f"{i+1}. {n} - {r}" for i, (n, r) in enumerate(data[:10])])

    embed = discord.Embed(title="PvP Top", description=text)

    await interaction.followup.send(embed=embed)


def calculate_pvp_rating(kills, deaths):
    if deaths == 0:
        return kills * 2
    return round((kills / deaths) * 100)


# ================= READY =================
@bot.event
async def on_ready():

    global db
    db = await asyncpg.create_pool(DATABASE_URL)

    async with db.acquire() as conn:
        await conn.execute("""
            CREATE TABLE IF NOT EXISTS applications(
                user_id BIGINT PRIMARY KEY,
                nickname TEXT,
                status TEXT
            )
        """)

    bot.add_view(ApplicationView(0, ""))  # persistent dummy (safe)
    await tree.sync()

    print("BOT READY")


bot.run(TOKEN)
