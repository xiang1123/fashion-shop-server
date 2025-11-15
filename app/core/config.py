from pydantic_settings import BaseSettings, SettingsConfigDict

class Settings(BaseSettings):
    APP_NAME: str = "fashion-shop"
    APP_ENV: str = "dev"
    APP_DEBUG: bool = True
    APP_SECRET_KEY: str = "change-me"
    ACCESS_TOKEN_EXPIRE_MINUTES: int = 60 * 24 * 30  # 30 days

    ALLOW_ORIGINS: str = "*"

    DB_HOST: str
    DB_PORT: int = 3306
    DB_USER: str
    DB_PASSWORD: str
    DB_NAME: str

    REDIS_URL: str = "redis://localhost:6379/0"

    ALIPAY_APP_ID: str
    ALIPAY_GATEWAY: str
    ALIPAY_APP_PRIVATE_KEY: str
    ALIPAY_PUBLIC_KEY: str
    ALIPAY_NOTIFY_URL: str
    ALIPAY_RETURN_URL: str

    # 新增这行（关键：要有类型注解）
    CLIENT_PAY_RESULT_URL: str = "http://localhost:5173"

    model_config = SettingsConfigDict(env_file=".env", env_file_encoding="utf-8")

    @property
    def SQLALCHEMY_DATABASE_URI(self) -> str:
        return f"mysql+pymysql://{self.DB_USER}:{self.DB_PASSWORD}@{self.DB_HOST}:{self.DB_PORT}/{self.DB_NAME}?charset=utf8mb4"

settings = Settings()