from mcrcon import MCRcon

RCON_HOST = "c11.play2go.cloud"
RCON_PORT = 20738
RCON_PASSWORD = "hfyG4v5SShHNLZhlVOtTZ0TotBvenJZtEkOuASq4MlsOZLYQ8stXFbbrblFvOWOeVjyU6o5TWu1WahKnKNJShXoIUEhsTbEPLDG"


def run_rcon(command: str):
    try:
        with MCRcon(RCON_HOST, RCON_PASSWORD, RCON_PORT) as mcr:
            response = mcr.command(command)
            return response
    except Exception as e:
        return f"RCON error: {e}"
