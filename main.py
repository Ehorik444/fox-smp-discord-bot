import os
import asyncio
import discord
import asyncpg
import json

from datetime import datetime, timedelta
from discord import app_commands
from discord.ui import Modal, TextInput, View
from dotenv import load_dotenv
from openai import OpenAI

load_dotenv()

# ================= CONFIG =================
TOKEN = os.getenv("DISCORD_TOKEN")
DATABASE_URL = os.getenv("DATABASE_URL")
OPENAI_API_KEY = os.getenv("OPENAI_API_KEY")

MOD_CHANNEL_ID = int(os.getenv("MOD_CHANNEL_ID", "0"))
LOG_CHANNEL_ID = int(os.getenv("LOG_CHANNEL_ID", "0"))
APPROVED_ROLE_ID = int(os.getenv("APPROVED_ROLE_ID", "0"))

AUTO_ACCEPT_SCORE = 85
AUTO_DECLINE_SCORE = 45
AI_ONLY_MODE = True

ai = OpenAI(api_key=OPENAI_API_KEY)

# ================= BOT =================
intents = discord.Intents.default()
intents.members = True

bot = discord.Client(intents=intents)
tree = app_commands.CommandTree(bot)

db = None

cooldowns = {}  # user_id -> datetime


# ================= LOG =================
async def log(text: str):
    ch = bot.get_channel(LOG_CHANNEL_ID)
    if ch:
        await ch.send(text)


# ================= SAFE AI =================
async def ai_score(nick, age, about):
    prompt = f"""
Оцени заявку игрока 0-100.

Верни ТОЛЬКО JSON:
{{
"score": число,
"reason": "кратко"
}}

Nick: {nick}
Age: {age}
About: {about}
"""

    try:
        res = await asyncio.to_thread(lambda: ai.chat.completions.create(
            model="gpt-4o-mini",
            messages=[
                {"role": "system", "content": "Ты строгий модератор Minecraft сервера"},
                {"role": "user", "content": prompt}
            ],
            temperature=0.2
        ))

        content = res.choices[0].message.content
        data = json.loads(content)

        return int(data.get("score", 50)), data.get("reason", "no reason")

    except:
        return 50, "AI error fallback"


# ================= MODAL =================
class ApplicationModal(Modal, title="Заявка"):
    nickname = TextInput(label="Nick")
    age = TextInput(label="Age")
    about = TextInput(label="About", style=discord.TextStyle.paragraph)

    async def on_submit(self, interaction: discord.Interaction):
        global db

        user_id = interaction.user.id
        now = datetime.utcnow()

        # cooldown
        if user_id in cooldowns and cooldowns[user_id] > now:
            await interaction.response.send_message("⏳ Кулдаун 24 часа", ephemeral=True)
            return

        cooldowns[user_id] = now + timedelta(hours=24)

        # duplicate check
        exists = await db.fetchrow(
            "SELECT status FROM applications WHERE user_id=$1 AND status='pending'",
            user_id
        )

        if exists:
            await interaction.response.send_message("❌ У тебя уже есть активная заявка", ephemeral=True)
            return

        try:
            age = int(self.age.value)
        except:
            await interaction.response.send_message("❌ Возраст должен быть числом", ephemeral=True)
            return

        score, reason = await ai_score(
            self.nickname.value,
            age,
            self.about.value
        )

        status = "pending"

        if AI_ONLY_MODE:
            if score >= AUTO_ACCEPT_SCORE:
                status = "accepted"
            elif score <= AUTO_DECLINE_SCORE:
                status = "declined"

        await db.execute("""
            INSERT INTO applications(user_id, nickname, status, score, created_at)
            VALUES($1,$2,$3,$4,$5)
            ON CONFLICT(user_id)
            DO UPDATE SET nickname=$2, status=$3, score=$4
        """, user_id, self.nickname.value, status, score, now)

        member = interaction.guild.get_member(user_id)

        # ===== AUTO ACCEPT =====
        if status == "accepted":
            role = interaction.guild.get_role(APPROVED_ROLE_ID)
            if member and role:
                await member.add_roles(role)

            try:
                await member.send("✅ Ты принят автоматически")
            except:
                pass

            await log(f"✅ AUTO ACCEPT {user_id} score={score}")

        # ===== AUTO DECLINE =====
        elif status == "declined":
            try:
                await member.send("❌ Ты отклонён автоматически")
            except:
                pass

            await log(f"❌ AUTO DECLINE {user_id} score={score}")

        # ===== MOD REVIEW =====
        else:
            ch = bot.get_channel(MOD_CHANNEL_ID)

            embed = discord.Embed(title="📨 Новая заявка")
            embed.add_field(name="User", value=str(user_id), inline=False)
            embed.add_field(name="Nick", value=self.nickname.value)
            embed.add_field(name="Score", value=str(score))
            embed.add_field(name="Reason", value=reason, inline=False)

            await ch.send(embed=embed, view=ApplicationView(user_id))

        await interaction.response.send_message("📨 Заявка отправлена", ephemeral=True)


# ================= MOD VIEW =================
class ApplicationView(View):
    def __init__(self, user_id: int):
        super().__init__(timeout=None)
        self.user_id = user_id

    @discord.ui.button(label="✅ Accept", style=discord.ButtonStyle.green)
    async def accept(self, interaction: discord.Interaction, button: discord.ui.Button):

        member = interaction.guild.get_member(self.user_id)
        role = interaction.guild.get_role(APPROVED_ROLE_ID)

        await db.execute(
            "UPDATE applications SET status='accepted' WHERE user_id=$1",
            self.user_id
        )

        if member and role:
            await member.add_roles(role)

        await log(f"MOD ACCEPT {self.user_id}")
        await interaction.response.send_message("Accepted", ephemeral=True)

    @discord.ui.button(label="❌ Decline", style=discord.ButtonStyle.red)
    async def decline(self, interaction: discord.Interaction, button: discord.ui.Button):

        await db.execute(
            "UPDATE applications SET status='declined' WHERE user_id=$1",
            self.user_id
        )

        await log(f"MOD DECLINE {self.user_id}")
        await interaction.response.send_message("Declined", ephemeral=True)


# ================= START PANEL =================
class StartView(View):
    @discord.ui.button(label="📨 Подать заявку", style=discord.ButtonStyle.primary)
    async def apply(self, interaction: discord.Interaction, button: discord.ui.Button):
        await interaction.response.send_modal(ApplicationModal())


@tree.command(name="zaiavka", description="Панель заявок")
async def zaiavka(interaction: discord.Interaction):

    if not interaction.user.guild_permissions.administrator:
        await interaction.response.send_message("❌ Нет прав", ephemeral=True)
        return

    embed = discord.Embed(title="📨 Система заявок")
    embed.description = "Нажми кнопку чтобы подать заявку"

    await interaction.response.send_message(embed=embed, view=StartView())


# ================= AI MOD HELPER =================
@tree.command(name="modai", description="AI помощник модератора")
async def modai(interaction: discord.Interaction, text: str):

    score, reason = await ai_score("unknown", 0, text)

    embed = discord.Embed(title="🧠 AI анализ")
    embed.add_field(name="Score", value=str(score))
    embed.add_field(name="Reason", value=reason, inline=False)

    await interaction.response.send_message(embed=embed, ephemeral=True)


# ================= GRAPH =================
@tree.command(name="graph", description="Статистика заявок")
async def graph(interaction: discord.Interaction):

    rows = await db.fetch("SELECT score FROM applications")

    scores = [r["score"] for r in rows]

    import matplotlib.pyplot as plt
    import io

    plt.figure()
    plt.hist(scores, bins=10)

    buf = io.BytesIO()
    plt.savefig(buf, format="png")
    buf.seek(0)
    plt.close()

    await interaction.response.send_message(file=discord.File(buf, "stats.png"))


# ================= READY =================
@bot.event
async def on_ready():
    global db

    db = await asyncpg.connect(DATABASE_URL)

    await db.execute("""
    CREATE TABLE IF NOT EXISTS applications(
        user_id BIGINT PRIMARY KEY,
        nickname TEXT,
        status TEXT,
        score INT,
        created_at TIMESTAMP
    )
    """)

    bot.add_view(StartView())

    await tree.sync()

    print("BOT READY")


bot.run(TOKEN)
