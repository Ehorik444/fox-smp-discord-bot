import os
from dotenv import load_dotenv

load_dotenv()

TOKEN = os.getenv("TOKEN")
GUILD_ID = int(os.getenv("GUILD_ID"))

VOICE_CATEGORY_ID = int(os.getenv("VOICE_CATEGORY_ID"))
TICKET_CATEGORY_ID = int(os.getenv("TICKET_CATEGORY_ID"))
