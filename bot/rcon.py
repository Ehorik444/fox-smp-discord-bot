from mcrcon import MCRcon

RCON_HOST = "localhost"
RCON_PORT = 25575
RCON_PASSWORD = "YOUR_PASSWORD"

def run_rcon(command: str):
    try:
        with MCRcon(RCON_HOST, RCON_PASSWORD, RCON_PORT) as mcr:
            return mcr.command(command)
    except Exception as e:
        print("[RCON ERROR]", e)
        return ""
