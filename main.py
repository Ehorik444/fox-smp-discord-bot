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


# ================= SAFE ENV =================
def env_int(name: str, default=0):
    v = os.getenv(name)
    return int(v) if v and v.isdigit() else default


def env_str(name: str, default=None):
    return os.getenv(name) or default


TOKEN = env_str("DISCORD_TOKEN")
DATABASE_URL = env_str("DATABASE_URL")

RCON_HOST = env_str("RCON_HOST")
RCON_PORT = env_int("RCON_PORT", 25575)
RCON_PASSWORD = env_str("RCON_PASSWORD")

MOD_CHANNEL_ID = env_int("MOD_CHANNEL_ID")

LEVEL_1_ROLE = env_int("LEVEL_1_ROLE")
LEVEL_2_ROLE = env_int("LEVEL_2_ROLE")
LEVEL_3_ROLE = env_int("LEVEL_3_ROLE")
LEVEL_4_ROLE = env_int("LEVEL_4_ROLE")


if not TOKEN:
    raise ValueError("DISCORD_TOKEN not set")

if not DATABASE_URL:
    raise ValueError("DATABASE_URL not set")


bot = discord.Client(intents=discord.Intents.all())
tree = app_commands.CommandTree(bot)

db = None


# ================= RCON =================
async def get_playtime(nick):
    try:
        def run():
            with MCRcon(RCON_HOST, RCON_PASSWORD, port=RCON_PORT) as mcr:
                return mcr.command(f"online total {nick}")

        return await asyncio.wait_for(asyncio.to_thread(run), timeout=5)
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
            try:
                await member.remove_roles(r)
            except:
                pass

    if roles[level]:
        try:
            await member.add_roles(roles[level])
        except:
            pass

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

        if not interaction.guild:
            await interaction.response.send_message("❌ Используй на сервере", ephemeral=True)
            return

        user_id = interaction.user.id

        row = await db.fetchrow(
            "SELECT status FROM applications WHERE user_id=$1",
            user_id
        )

        if row and row["status"] == "pending":
            await interaction.response.send_message("❌ Уже есть заявка", ephemeral=True)
            return

        try:
            age = int(self.age.value)
        except ValueError:
            await interaction.response.send_message("❌ Возраст должен быть числом", ephemeral=True)
            return

        about = self.about.value

        await db.execute("""
            INSERT INTO applications (user_id, nickname, status)
            VALUES ($1,$2,'pending')
            ON CONFLICT (user_id)
            DO UPDATE SET nickname=$2,status='pending'
        """, user_id, self.nickname.value)

        mod = bot.get_channel(MOD_CHANNEL_ID)

        if not mod:
            await interaction.response.send_message("❌ Канал модерации не найден", ephemeral=True)
            return

        embed = discord.Embed(title="📨 Заявка")

        embed.add_field(name="UserID", value=str(user_id))
        embed.add_field(name="Nick", value=self.nickname.value)
        embed.add_field(name="Age", value=str(age))
        embed.add_field(name="About", value=about)

        if age >= 14 and len(about) >= 32:

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

        if not interaction.message.embeds:
            await interaction.response.send_message("❌ Ошибка данных", ephemeral=True)
            return

        try:
            user_id = int(interaction.message.embeds[0].fields[0].value)
        except:
            await interaction.response.send_message("❌ Не удалось получить user_id", ephemeral=True)
            return

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

    level = await update_level(interaction.user, hours)

    url = f"http://YOUR_SERVER:8804/v1/player/{nick}/activity?period=7"

    try:
        async with aiohttp.ClientSession() as s:
            async with s.get(url) as r:
                if r.status != 200:
                    raise Exception()
                data = await r.json()
    except:
        await interaction.response.send_message("❌ Ошибка получения данных", ephemeral=True)
        return

    if not data:
        await interaction.response.send_message("❌ Нет данных активности", ephemeral=True)
        return

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
    embed.add_field(name="Hours", value=str(hours))
    embed.add_field(name="Level", value=str(level))

    await interaction.response.send_message(embed=embed, file=file)


@tree.command(name="pvp_top_global", description="Топ PvP игроков")
async def pvp_top_global(interaction: discord.Interaction):
    await interaction.response.defer()

    try:
        async with aiohttp.ClientSession() as s:
            async with s.get("http://YOUR_SERVER:8804/v1/players") as r:
                players = await r.json()
    except:
        await interaction.followup.send("❌ Ошибка API")
        return

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

    print("BOT STARTING...")

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
