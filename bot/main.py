import discord
from discord import app_commands
from config import TOKEN
from minecraft import get_server_status
from tickets import create_ticket
from voice import create_voice

intents = discord.Intents.all()
bot = discord.Client(intents=intents)
tree = app_commands.CommandTree(bot)


# ---------------- STATUS ----------------
@tree.command(name="server", description="Статус SMP сервера")
async def server(interaction: discord.Interaction):
    data = get_server_status()

    players = ", ".join(data["players"]) if data["players"] else "никого"
    await interaction.response.send_message(
        f"🟢 Онлайн: {data['online']}\n"
        f"👥 Игроки: {players} ({len(data['players'])}/{data['max']})"
    )


# ---------------- TICKET ----------------
@tree.command(name="report", description="Пожаловаться на игрока")
@app_commands.describe(reason="Опиши проблему")
async def report(interaction: discord.Interaction, reason: str):
    await create_ticket(interaction, reason)


# ---------------- VOICE ----------------
@tree.command(name="voice", description="Создать приватный войс")
async def voice(interaction: discord.Interaction):
    await create_voice(interaction)


# ---------------- LINK ACCOUNT ----------------
@tree.command(name="link", description="Привязка Minecraft аккаунта")
async def link(interaction: discord.Interaction, nick: str):
    from database import links
    links[interaction.user.id] = nick

    await interaction.response.send_message(
        f"🔗 Привязан Minecraft ник: {nick}",
        ephemeral=True
    )


# ---------------- START ----------------
@bot.event
async def on_ready():
    await tree.sync()
    print(f"Bot ready as {bot.user}")


bot.run(TOKEN)
