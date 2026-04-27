last_players = None

async def minecraft_to_discord(bot, channel_id):
    global last_players

    channel = bot.get_channel(channel_id)
    if not channel:
        return

    raw = run_rcon("list")

    players = set()

    if raw and ":" in raw:
        try:
            part = raw.split(":")[1].strip()
            players = set(p.strip() for p in part.split(",") if p.strip())
        except:
            players = set()

    if last_players is None:
        last_players = players
        return

    if players == last_players:
        return

    joined = players - last_players
    left = last_players - players

    for p in joined:
        await channel.send(f"🟢 {p} зашёл на сервер")

    for p in left:
        await channel.send(f"🔴 {p} вышел с сервера")

    last_players = players
