from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_file=".env", extra="ignore")

    # Connexion Postgres. En docker-compose, surchargée par la variable
    # d'environnement DATABASE_URL (voir docker-compose.yml).
    database_url: str = (
        "postgresql+psycopg://boucherie:boucherie@localhost:5432/boucherie"
    )

    # Origines autorisées pour le front Refine (Vite = 5173, CRA = 3000).
    cors_origins: str = "http://localhost:5173,http://localhost:3000"

    # --- Copilote IA (Claude) ---
    # Le SDK Anthropic lit ANTHROPIC_API_KEY dans l'environnement ; on la
    # reprend ici juste pour savoir si le copilote est configuré.
    anthropic_api_key: str = ""
    copilot_model: str = "claude-opus-4-8"
    # Connexion Postgres LECTURE SEULE utilisée par l'outil SQL du copilote
    # (rôle grafana_ro : SELECT uniquement). Surchargée en docker-compose.
    copilot_database_url: str = (
        "postgresql+psycopg://grafana_ro:grafana_ro@localhost:5432/boucherie"
    )

    # En dev : crée les tables au démarrage via metadata.create_all.
    # ⚠️ À passer à False dès qu'on bascule sur les migrations Alembic
    # (obligatoire avant la première mise en prod avec de vraies données).
    dev_create_all: bool = True

    @property
    def cors_origins_list(self) -> list[str]:
        return [o.strip() for o in self.cors_origins.split(",") if o.strip()]


settings = Settings()
