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
RCON_PORT = int(os.getenv("RCON_PORT", "25575"))
RCON_PASSWORD = os.getenv("RCON_PASSWORD")

MOD_CHANNEL_ID = int(os.getenv("MOD_CHANNEL_ID", "0"))

# SAFE ROLE PARSING (fix crash)
def get_role(env_name):
    v = os.getenv(env_name)
    return int(v) if v and v.isdigit() else 0

LEVEL_1_ROLE = get_role("LEVEL_1_ROLE")
LEVEL_2_ROLE = get_role("LEVEL_2_ROLE")
LEVEL_3_ROLE = get_role("LEVEL_3_ROLE")
LEVEL_4_ROLE = get_role("LEVEL_4_ROLE")

bot = discord.Client(intents=discord.Intents.all())
tree = app_commands.CommandTree(bot)

db = None


# ================= RCON =================
async def get_playtime(nick):
    try:
        def run():
            with MCRcon(RCON_HOST, RCON_PASSWORD, port=RCON_PORT) as mcr:
                return mcr.command(f"online total {nick}")

        return await asyncio.to_thread(run)

    except:
        return "0 hours"


def parse_hours(text: str):
    h = re.findall(r"(\d+)\s*hour", text)
    m = re.findall(r"(\d+)\s*minute", text)

    hours = sum(map(int, h)) if h else 0
    minutes = sum(map(int, m)) if m else 0

    return hours + minutes // 60


# ================= LEVEL =================
async def update_level(member, hours):
    if not member:
        return 1

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


# ================= MODAL =================
class ApplicationModal(Modal, title="Заявка"):
    nickname = TextInput(label="Minecraft ник")
    age = TextInput(label="Возраст")
    about = TextInput(label="О себе", style=discord.TextStyle.paragraph)

    async def on_submit(self, interaction: discord.Interaction):

        global db

        if db is None:
            await interaction.response.send_message("DB not ready", ephemeral=True)
            return

        user_id = interaction.user.id

        row = await db.fetchrow(
            "SELECT status FROM applications WHERE user_id=$1",
            user_id
        )

        if row and row["status"] == "pending":
            await interaction.response.send_message("❌ Уже есть заявка", ephemeral=True)
            return

        age = int(self.age.value)
        about = self.about.value

        await db.execute("""
            INSERT INTO applications (user_id, nickname, status)
            VALUES ($1,$2,'pending')
            ON CONFLICT (user_id)
            DO UPDATE SET nickname=$2,status='pending'
        """, user_id, self.nickname.value)

        mod = bot.get_channel(MOD_CHANNEL_ID)

        embed = discord.Embed(title="📨 Заявка")

        embed.add_field(name="UserID", value=str(user_id))
        embed.add_field(name="Nick", value=self.nickname.value)
        embed.add_field(name="Age", value=age)
        embed.add_field(name="About", value=about)

        if age >= 14 and len(about) >= 32:

            member = interaction.guild.get_member(user_id)

            await db.execute("""
                UPDATE applications SET status='accepted'
                WHERE user_id=$1
            """, user_id)

            embed.color = 0x00ff00
            embed.add_field(name="Status", value="AUTO ACCEPT")

            await mod.send(embed=embed)
            await interaction.response.send_message("✅ Принят", ephemeral=True)

        else:
            await mod.send(embed=embed, view=ApplicationView())
            await interaction.response.send_message("📨 Отправлено", ephemeral=True)


# ================= VIEW =================
class ApplicationView(View):
    def __init__(self):
        super().__init__(timeout=None)

    @discord.ui.button(label="Принять", style=discord.ButtonStyle.green, custom_id="accept")
    async def accept(self, interaction, button):

        global db

        user_id = int(interaction.message.embeds[0].fields[0].value)

        await db.execute("""
            UPDATE applications SET status='accepted'
            WHERE user_id=$1
        """, user_id)

        await interaction.response.send_message("✅ Принято")


# ================= COMMANDS =================
@tree.command(name="apply", description="Подать заявку")
async def apply(interaction: discord.Interaction):
    await interaction.response.send_modal(ApplicationModal())


@tree.command(name="profile", description="Профиль игрока")
async def profile(interaction: discord.Interaction):

    global db

    if db is None:
        await interaction.response.send_message("DB not ready", ephemeral=True)
        return

    row = await db.fetchrow(
        "SELECT nickname FROM applications WHERE user_id=$1",
        interaction.user.id
    )

    if not row:
        await interaction.response.send_message("❌ Нет заявки", ephemeral=True)
        return

    nick = row["nickname"]

    play = await get_playtime(nick)
    hours = parse_hours(play)

    member = interaction.user
    level = await update_level(member, hours)

    url = f"http://YOUR_SERVER:8804/v1/player/{nick}/activity?period=7"

    async with aiohttp.ClientSession() as s:
        async with s.get(url) as r:
            data = await r.json()

    days = [d["date"] for d in data]
    vals = [d["activity"] for d in data]

    plt.plot(days, vals)
    buf = io.BytesIO()
    plt.savefig(buf, format="png")
    buf.seek(0)
    plt.close()

    file = discord.File(buf, "graph.png")

    embed = discord.Embed(title="Профиль")
    embed.add_field(name="Nick", value=nick)
    embed.add_field(name="Hours", value=hours)
    embed.add_field(name="Level", value=level)

    await interaction.response.send_message(embed=embed, file=file)


@tree.command(name="pvp_top_global", description="Топ PvP игроков")
async def pvp_top_global(interaction: discord.Interaction):

    await interaction.response.defer()

    async with aiohttp.ClientSession() as s:
        async with s.get("http://YOUR_SERVER:8804/v1/players") as r:
            players = await r.json()

    def rating(k, d):
        return 0 if d == 0 else round((k / d) * 100)

    data = [(p["name"], rating(p.get("kills", 0), p.get("deaths", 0))) for p in players]
    data.sort(key=lambda x: x[1], reverse=True)

    text = "\n".join([f"{i+1}. {n} - {r}" for i, (n, r) in enumerate(data[:10])])

    embed = discord.Embed(title="PvP Top", description=text)

    await interaction.followup.send(embed=embed)


# ================= READY =================
@bot.event
async def on_ready():

    global db

    db = await asyncpg.connect(DATABASE_URL)

    await db.execute("""
        CREATE TABLE IF NOT EXISTS applications(
            user_id BIGINT PRIMARY KEY,
            nickname TEXT,
            status TEXT
        )
    """)

    bot.add_view(ApplicationView())

    print("SYNCING COMMANDS...")
    await tree.sync()
    print("BOT READY")


bot.run(TOKEN)
