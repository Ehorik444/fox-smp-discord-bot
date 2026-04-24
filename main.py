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
import json

from discord import app_commands
from discord.ui import Modal, TextInput, View
from dotenv import load_dotenv
from mcrcon import MCRcon
from openai import OpenAI

load_dotenv()

# ================= ENV =================
def env_int(name, default=0):
    v = os.getenv(name)
    return int(v) if v and v.isdigit() else default


def env_str(name, default=None):
    return os.getenv(name) or default


TOKEN = env_str("DISCORD_TOKEN")
DATABASE_URL = env_str("DATABASE_URL")
OPENAI_API_KEY = env_str("OPENAI_API_KEY")

MOD_CHANNEL_ID = env_int("MOD_CHANNEL_ID")
LOG_CHANNEL_ID = env_int("LOG_CHANNEL_ID")
APPROVED_ROLE_ID = env_int("APPROVED_ROLE_ID")

AI_ONLY_MODE = True
AUTO_ACCEPT_SCORE = 85
AUTO_DECLINE_SCORE = 45

ai_client = OpenAI(api_key=OPENAI_API_KEY)

# ================= BOT =================
intents = discord.Intents.default()
intents.members = True

bot = discord.Client(intents=intents)
tree = app_commands.CommandTree(bot)

db = None
cooldowns = {}

# ================= LOG =================
async def log_action(text):
    ch = bot.get_channel(LOG_CHANNEL_ID)
    if ch:
        try:
            await ch.send(text)
        except:
            pass


# ================= AI SCORE =================
async def ai_score_application(age, about, nick):
    prompt = f"""
Оцени заявку 0-100.

Верни JSON:
{{
"score": число,
"reason": "кратко"
}}

Nick: {nick}
Age: {age}
About: {about}
"""

    try:
        res = await asyncio.to_thread(
            lambda: ai_client.chat.completions.create(
                model="gpt-4o-mini",
                messages=[
                    {"role": "system", "content": "Ты строгий модератор Minecraft сервера"},
                    {"role": "user", "content": prompt}
                ],
                temperature=0.3
            )
        )
        return res.choices[0].message.content
    except:
        return '{"score":50,"reason":"error"}'


# ================= MODAL =================
class ApplicationModal(Modal, title="Заявка"):
    nickname = TextInput(label="Nick")
    age = TextInput(label="Age")
    about = TextInput(label="About", style=discord.TextStyle.paragraph)

    async def on_submit(self, interaction: discord.Interaction):
        global db

        user_id = interaction.user.id

        if db is None:
            await interaction.response.send_message("DB not ready", ephemeral=True)
            return

        # cooldown
        if user_id in cooldowns:
            if cooldowns[user_id] > discord.utils.utcnow():
                await interaction.response.send_message("⏳ cooldown", ephemeral=True)
                return

        cooldowns[user_id] = discord.utils.utcnow() + discord.timedelta(hours=24)

        # anti spam DB
        row = await db.fetchrow("SELECT status FROM applications WHERE user_id=$1", user_id)
        if row and row["status"] == "pending":
            await interaction.response.send_message("❌ already exists", ephemeral=True)
            return

        try:
            age = int(self.age.value)
        except:
            await interaction.response.send_message("age must be number", ephemeral=True)
            return

        # AI
        ai_raw = await ai_score_application(age, self.about.value, self.nickname.value)

        try:
            data = json.loads(ai_raw)
            score = data["score"]
            reason = data["reason"]
        except:
            score = 50
            reason = "parse error"

        status = "pending"

        if AI_ONLY_MODE:
            if score >= AUTO_ACCEPT_SCORE:
                status = "accepted"
            elif score <= AUTO_DECLINE_SCORE:
                status = "declined"

        await db.execute("""
        INSERT INTO applications(user_id,nickname,status,score)
        VALUES($1,$2,$3,$4)
        ON CONFLICT(user_id)
        DO UPDATE SET nickname=$2,status=$3,score=$4
        """, user_id, self.nickname.value, status, score)

        member = interaction.guild.get_member(user_id)

        # AUTO ACCEPT
        if status == "accepted":
            role = interaction.guild.get_role(APPROVED_ROLE_ID)
            if role and member:
                try:
                    await member.add_roles(role)
                except:
                    pass

            try:
                await member.send("✅ Ты принят AI системой")
            except:
                pass

            await log_action(f"AI ACCEPT {user_id} score={score}")

        # AUTO DECLINE
        elif status == "declined":
            try:
                await member.send("❌ Ты отклонён AI системой")
            except:
                pass

            await log_action(f"AI DECLINE {user_id} score={score}")

        # MANUAL REVIEW
        else:
            mod = bot.get_channel(MOD_CHANNEL_ID)

            embed = discord.Embed(title="📨 Review")
            embed.add_field(name="Nick", value=self.nickname.value)
            embed.add_field(name="Score", value=str(score))
            embed.add_field(name="Reason", value=reason, inline=False)

            await mod.send(embed=embed, view=ApplicationView())

        await interaction.response.send_message("sent", ephemeral=True)


# ================= VIEW =================
class ApplicationView(View):
    def __init__(self):
        super().__init__(timeout=None)

    @discord.ui.button(label="Accept", style=discord.ButtonStyle.green)
    async def accept(self, interaction, button):

        user_id = int(interaction.message.embeds[0].fields[0].value)

        await db.execute("UPDATE applications SET status='accepted' WHERE user_id=$1", user_id)

        member = interaction.guild.get_member(user_id)
        role = interaction.guild.get_role(APPROVED_ROLE_ID)

        if member and role:
            try:
                await member.add_roles(role)
            except:
                pass

        await log_action(f"MOD ACCEPT {user_id}")

        await interaction.response.send_message("ok")


    @discord.ui.button(label="Decline", style=discord.ButtonStyle.red)
    async def decline(self, interaction, button):

        user_id = int(interaction.message.embeds[0].fields[0].value)

        await db.execute("UPDATE applications SET status='declined' WHERE user_id=$1", user_id)

        await log_action(f"MOD DECLINE {user_id}")

        await interaction.response.send_message("ok")


# ================= START PANEL =================
class StartView(View):
    @discord.ui.button(label="📨 Apply", style=discord.ButtonStyle.primary)
    async def start(self, interaction, button):
        await interaction.response.send_modal(ApplicationModal())


@tree.command(name="zaiavka", description="panel")
async def zaiavka(interaction: discord.Interaction):

    if not interaction.user.guild_permissions.administrator:
        await interaction.response.send_message("no perms", ephemeral=True)
        return

    embed = discord.Embed(title="Apply system")

    await interaction.response.send_message(embed=embed, view=StartView())


# ================= AI MOD CHAT =================
@tree.command(name="modai", description="AI mod helper")
async def modai(interaction: discord.Interaction, text: str):

    if not interaction.user.guild_permissions.administrator:
        await interaction.response.send_message("no perms", ephemeral=True)
        return

    res = await ai_score_application(0, text, "unknown")

    try:
        data = json.loads(res)
    except:
        await interaction.response.send_message("error", ephemeral=True)
        return

    embed = discord.Embed(title="AI MOD")

    embed.add_field(name="score", value=str(data["score"]))
    embed.add_field(name="reason", value=data["reason"], inline=False)

    await interaction.response.send_message(embed=embed, ephemeral=True)


# ================= GRAPH =================
@tree.command(name="graph", description="quality graph")
async def graph(interaction: discord.Interaction):

    rows = await db.fetch("SELECT score FROM applications")

    scores = [r["score"] for r in rows]

    plt.figure()
    plt.hist(scores, bins=10)

    buf = io.BytesIO()
    plt.savefig(buf, format="png")
    buf.seek(0)
    plt.close()

    await interaction.response.send_message(file=discord.File(buf, "g.png"))


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
        score INT DEFAULT 0
    )
    """)

    bot.add_view(StartView())
    bot.add_view(ApplicationView())

    await tree.sync()

    print("READY")


bot.run(TOKEN)
