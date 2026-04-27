import discord
from rcon import run_rcon

DISCORD_CHANNEL_ID = 123456789  # поставь свой ID


# Discord → Minecraft
async def discord_to_mc(message: discord.Message):
    try:
        if message.author.bot:
            return

        content = message.content[:200]

        run_rcon(f"say [Discord] {message.author.name}: {content}")

    except Exception as e:
        print("Discord->MC error:", e)


# Minecraft → Discord (join/leave через /list)
async def minecraft_to_discord(bot):
    try:
        raw = run_rcon("list")

        players = set()

        if ":" in raw:
            try:
                players = set(raw.split(":")[1].strip().split(", "))
            except:
                pass

        channel = bot.get_channel(DISCORD_CHANNEL_ID)

        if not hasattr(minecraft_to_discord, "last"):
            minecraft_to_discord.last = set()

        joined = players - minecraft_to_discord.last
        left = minecraft_to_discord.last - players

        for p in joined:
            await channel.send(f"🟢 {p} зашёл на сервер")

        for p in left:
            await channel.send(f"🔴 {p} вышел с сервера")

        minecraft_to_discord.last = players

        return players

    except Exception as e:
        print("MC->Discord error:", e)
        return set()
