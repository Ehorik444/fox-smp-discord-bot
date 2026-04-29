import os
from dotenv import load_dotenv

load_dotenv()

TOKEN = os.getenv("TOKEN")

DATABASE_URL = os.getenv("DATABASE_URL")

APPLICATION_LOG_CHANNEL = int(os.getenv("APPLICATION_LOG_CHANNEL", "0"))
GUILD_ID = int(os.getenv("GUILD_ID", "0"))
