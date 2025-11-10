from datetime import datetime

from alu_helper.database import connect
from pydantic import BaseModel, field_validator


class Settings(BaseModel):
    initial_data_loaded: bool = False
    window_geometry: str = ""
    window_state: str = ""

    show_tray_icon: bool = False
    close_to_tray: bool = False
    start_minimized: bool = False

    daily_gift_link: str = "https://shop.gameloft.com/games/Asphalt_Unite"
    daily_gift_timer: bool = False
    daily_gift_notification: bool = True
    next_daily_gift_time: datetime | None = None

    @field_validator("next_daily_gift_time", mode="before")
    @classmethod
    def parse_next_daily_gift_time(cls, v):
        if v is None:
            return None
        if isinstance(v, str):
            if v == "None" or v == "":
                return None
            return datetime.fromisoformat(v)
        if isinstance(v, datetime):
            return v
        return None

class SettingsRepository:

    def save(self, key: str, value: str):
        with connect() as conn:
            conn.execute("INSERT OR REPLACE INTO settings(`key`, value) VALUES (:key, :value)", {"key": key, "value": value})

    def get_all(self):
        with connect() as conn:
            rows = conn.execute("SELECT * FROM settings").fetchall()
            data = {row["key"]: row["value"] for row in rows}
            return Settings(**data)


class SettingsService:
    cache = None

    def __init__(self, repo: SettingsRepository):
        self.repo = repo

    def save(self, settings: Settings):
        for key, value1 in self.get().model_dump().items():
            value2 = getattr(settings, key)
            if value1 != value2:
                self.repo.save(key, str(value2))
        self.cache = None

    def get(self) -> Settings:
        if not self.cache:
            self.cache = self.repo.get_all()
        return Settings(**self.cache.model_dump())