from rcon import run_rcon
import discord


async def discord_to_mc(message):
    try:
        run_rcon(f"say [Discord] {message.author.name}: {message.content}")

    except Exception as e:
        print("Discord->MC error:", e)


async def minecraft_to_discord(bot, channel_id):
    try:
        channel = bot.get_channel(channel_id)

        if channel is None:
            print("Channel not found!")
            return

        raw = run_rcon("list")

        players = set()

        if ":" in raw:
            try:
                players = set(raw.split(":")[1].strip().split(", "))
            except:
                pass

        await channel.send(f"🟢 Online: {', '.join(players) if players else 'no players'}")

    except Exception as e:
        print("MC->Discord error:", e)
