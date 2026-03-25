import os
from dotenv import load_dotenv

load_dotenv()

BOT_TOKEN = os.getenv("BOT_TOKEN", "8223193856:AAGKF0IfbMVC6anb4wsJR2D6dJsNrQiDhaI")
CHANNEL_ID = os.getenv("CHANNEL_ID", "")
FETCH_INTERVAL = int(os.getenv("FETCH_INTERVAL", "300"))
ITEMS_PER_BATCH = int(os.getenv("ITEMS_PER_BATCH", "6"))
DB_PATH = os.getenv("DB_PATH", "data/operatorzero.db")
