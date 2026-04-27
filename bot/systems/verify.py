import random
from rcon import run_rcon

pending = {}


def generate_code():
    return str(random.randint(1000, 9999))


async def start_verification(discord_id, minecraft_name):
    code = generate_code()
    pending[discord_id] = (minecraft_name, code)

    run_rcon(f"tell {minecraft_name} Your code: {code}")

    return code


def check_code(discord_id, code):
    if discord_id not in pending:
        return False

    mc_name, real_code = pending[discord_id]

    if code == real_code:
        del pending[discord_id]
        return mc_name

    return False
