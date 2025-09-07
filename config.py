from pydantic import BaseModel
import os

class Config(BaseModel):
    BOT_TOKEN: str
    ADMIN_ID: int

config = Config(
    BOT_TOKEN=os.getenv("BOT_TOKEN", ""),
    ADMIN_ID=int(os.getenv("ADMIN_ID", ""))
)