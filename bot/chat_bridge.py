import discord
from rcon import run_rcon

DISCORD_CHANNEL_ID = 123456789  # канал чата в Discord


# ---------- Discord → Minecraft ----------
async def discord_to_mc(message: discord.Message):
    if message.author.bot:
        return

    content = message.content.replace('"', "'")

    # отправка в Minecraft чат
    run_rcon(f'say [Discord] {message.author.name}: {content}')


# ---------- Minecraft → Discord ----------
# простой polling через /list + кастомный лог (ограниченно)
last_players = set()

async def minecraft_to_discord(bot: discord.Client):
    global last_players

    raw = run_rcon("list")

    players = set()

    if ":" in raw:
        try:
            players = set(raw.split(":")[1].strip().split(", "))
        except:
            players = set()

    joined = players - last_players
    left = last_players - players

    channel = bot.get_channel(DISCORD_CHANNEL_ID)

    for p in joined:
        await channel.send(f"🟢 **{p}** зашёл на сервер")

    for p in left:
        await channel.send(f"🔴 **{p}** вышел с сервера")

    last_players = players
