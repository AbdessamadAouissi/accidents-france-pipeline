"""Configuration centralisée via Pydantic Settings."""

from pathlib import Path

from pydantic import Field
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        case_sensitive=False,
        extra="ignore",
        protected_namespaces=(),  # autorise les champs "model_*" sans warning
    )

    # Application
    app_env: str = "dev"
    log_level: str = "INFO"

    # Répertoires
    project_root: Path = Path(__file__).resolve().parents[2]
    data_dir: Path = Field(default=Path("./data"))
    raw_dir: Path = Field(default=Path("./data/raw"))
    processed_dir: Path = Field(default=Path("./data/processed"))
    warehouse_dir: Path = Field(default=Path("./data/warehouse"))
    model_dir: Path = Field(default=Path("./models"))

    # DuckDB
    duckdb_path: Path = Field(default=Path("./data/warehouse/accidents.duckdb"))

    # Sources
    onisr_years: str = "2021,2022,2023,2024"

    # API
    api_host: str = "0.0.0.0"
    api_port: int = 8000
    api_prefix: str = "/api/v1"

    # ML
    random_seed: int = 42

    @property
    def years(self) -> list[int]:
        return [int(y) for y in self.onisr_years.split(",") if y.strip()]

    def ensure_dirs(self) -> None:
        for p in [
            self.data_dir,
            self.raw_dir,
            self.processed_dir,
            self.warehouse_dir,
            self.model_dir,
        ]:
            Path(p).mkdir(parents=True, exist_ok=True)


settings = Settings()
settings.ensure_dirs()
