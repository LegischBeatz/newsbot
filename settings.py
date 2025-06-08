from dataclasses import dataclass
from pathlib import Path
import configparser

BASE_DIR = Path(__file__).resolve().parent
DB_PATH = BASE_DIR / "news_articles.db"
CONFIG_PATH = BASE_DIR / "config.ini"


@dataclass(frozen=True)
class Config:
    """Application configuration loaded from ``config.ini``."""

    bearer_token: str
    api_key: str
    api_secret: str
    access_token: str
    access_token_secret: str
    llm_api_url: str
    model_name: str
    debug_mode: bool

    @classmethod
    def load(cls, path: Path = CONFIG_PATH) -> "Config":
        parser = configparser.ConfigParser(interpolation=None)
        parser.read(path)
        tw = parser["TwitterAPI"]
        llm = parser["LLM"]
        settings = parser["Settings"]
        return cls(
            bearer_token=tw["bearer_token"],
            api_key=tw["api_key"],
            api_secret=tw["api_secret"],
            access_token=tw["access_token"],
            access_token_secret=tw["access_token_secret"],
            llm_api_url=llm["api_url"],
            model_name=llm["model_name"],
            debug_mode=settings.getboolean("debug_mode", fallback=False),
        )
