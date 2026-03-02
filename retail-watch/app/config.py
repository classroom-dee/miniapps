from dataclasses import dataclass
from pathlib import Path

from fastapi.templating import Jinja2Templates


@dataclass
class Settings:
    database_url: str


PROJECT_PATH = Path(__file__).resolve().parent
settings = Settings(database_url="sqlite:///dev.db")
templates = Jinja2Templates(directory=PROJECT_PATH / "templates")
