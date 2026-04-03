from pydantic_settings import BaseSettings


class Settings(BaseSettings):
    app_name: str = "TEZ Execution System API"
    app_env: str = "development"
    api_v1_prefix: str = "/api/v1"
    docs_url: str = "/api-docs"
    openapi_url: str = "/api/v1/openapi.json"
    redoc_url: str = "/api-redoc"


settings = Settings()
