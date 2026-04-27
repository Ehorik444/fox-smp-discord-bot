import os
from dotenv import load_dotenv

load_dotenv()

TOKEN = os.getenv("TOKEN")

GUILD_ID = os.getenv("GUILD_ID")
VOICE_CATEGORY_ID = os.getenv("VOICE_CATEGORY_ID")
TICKET_CATEGORY_ID = os.getenv("TICKET_CATEGORY_ID")

# защита от None
if GUILD_ID:
    GUILD_ID = int(GUILD_ID)
else:
    raise ValueError("GUILD_ID не задан в .env")

if VOICE_CATEGORY_ID:
    VOICE_CATEGORY_ID = int(VOICE_CATEGORY_ID)

if TICKET_CATEGORY_ID:
    TICKET_CATEGORY_ID = int(TICKET_CATEGORY_ID)
