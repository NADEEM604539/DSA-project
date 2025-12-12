"""
config.py

Role: Required configuration for the backend.
- Holds DB connection settings from .env file
- Holds DSA tuning options (hash table size, trie limits)
- Backend is API-first: User creation via frontend API calls (Clerk auth in frontend)

Security note:
- Database credentials are in .env file and NOT committed to version control
- For production, use environment variables for sensitive data
"""

from pydantic import Field
from pydantic_settings import BaseSettings


class Settings(BaseSettings):
    # ----- Database (defaults you provided) -----
    DB_USER: str = Field("root", env="DB_USER")
    DB_PASSWORD: str = Field("NdM604539", env="DB_PASSWORD")
    DB_HOST: str = Field("127.0.0.1", env="DB_HOST")
    DB_PORT: int = Field(3306, env="DB_PORT")
    DB_NAME: str = Field("library", env="DB_NAME")

    # SQLAlchemy URL using pymysql driver
    SQLALCHEMY_DATABASE_URL: str = Field(
        default="",
        env="SQLALCHEMY_DATABASE_URL",
        description="If provided, overrides automatic URL build"
    )

    # ----- DSA tuning (small knobs) -----
    HASH_TABLE_SIZE: int = Field(4096, env="HASH_TABLE_SIZE")
    TRIE_SUGGEST_LIMIT: int = Field(20, env="TRIE_SUGGEST_LIMIT")

    class Config:
        env_file = ".env"
        env_file_encoding = "utf-8"

    @property
    def database_url(self) -> str:
        # if user provided full URL via env, use it; otherwise build from components
        if self.SQLALCHEMY_DATABASE_URL:
            return self.SQLALCHEMY_DATABASE_URL
        return (
            f"mysql+pymysql://{self.DB_USER}:"
            f"{self.DB_PASSWORD}@{self.DB_HOST}:"
            f"{self.DB_PORT}/{self.DB_NAME}?charset=utf8mb4"
        )


# instantiate a single settings object for import elsewhere
settings = Settings()
