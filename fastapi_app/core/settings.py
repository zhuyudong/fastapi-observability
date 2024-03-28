from decouple import config
from pydantic_settings import BaseSettings


class Settings(BaseSettings):
    PROMETHEUS_ENABLE: str = config("PROMETHEUS_ENABLE", default="true")

    # class Config:
    #     case_sensitive = True
    #     env_prefix = "PORTAL_"
    #     env_file = f"{PROJECT_ROOT}/.env.local"
    #     validate_assignment = True


settings = Settings()  # type: ignore[call-arg]
