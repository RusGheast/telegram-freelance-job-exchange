from pydantic import BaseModel
import os
from dotenv import load_dotenv

load_dotenv()

class Config(BaseModel):
    BOT_TOKEN: str
    ADMIN_ID: int

config = Config(
    BOT_TOKEN=os.getenv("BOT_TOKEN"),
    ADMIN_ID=os.getenv("ADMIN_ID")
)