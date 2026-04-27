from mcrcon import MCRcon

RCON_HOST = "c11.play2go.cloud"
RCON_PORT = 20837
RCON_PASSWORD = "YOUR_PASSWORD"


def run_rcon(command: str):
    try:
        with MCRcon(RCON_HOST, RCON_PASSWORD, RCON_PORT) as mcr:
            response = mcr.command(command)
            return response
    except Exception as e:
        return f"RCON error: {e}"
