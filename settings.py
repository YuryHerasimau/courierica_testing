from pydantic_settings import BaseSettings


class Settings(BaseSettings):
    BASE_URL: str

    ADMIN_USERNAME: str
    ADMIN_PASSWORD: str

    LOGISTICIAN_SAAS_USERNAME: str
    LOGISTICIAN_SAAS_PASSWORD: str

    COURIER_SAAS_PHONE: str
    COURIER_SAAS_CODE: str
    COURIER_SAAS_ID: str

    LOGISTICIAN_IIKO_USERNAME: str
    LOGISTICIAN_IIKO_PASSWORD: str

    IIKO_API_LOGIN: str

    class Config:
        env_file = ".env"


settings = Settings()