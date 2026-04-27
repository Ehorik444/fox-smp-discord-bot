from rcon import run_rcon

def get_server_status():
    try:
        # Получаем список игроков через RCON
        raw = run_rcon("list")

        # Пример ответа:
        # "There are 2 of a max of 20 players online: Steve, Alex"

        players = []

        if ":" in raw:
            parts = raw.split(":")
            if len(parts) > 1:
                players = [p.strip() for p in parts[1].split(",") if p.strip()]

        return {
            "online": True,
            "players": players,
            "max": 20
        }

    except:
        return {
            "online": False,
            "players": [],
            "max": 20
        }
