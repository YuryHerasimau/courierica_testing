import os
from pydantic import field_validator
from pydantic_settings import BaseSettings


class Settings(BaseSettings):
    TEST_ENV: str = "dev"

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
    IIKO_ORGANIZATION_ID: str
    COURIERICA_PICKUP_POINT_ID: str

    COURIER_COMPANY_ID: str
    COURIER_PICKUP_POINT_ID: str

    class Config:
        env_file = f".env.{os.getenv('TEST_ENV', 'dev')}"

    @field_validator("TEST_ENV")
    def check_env(cls, v):
        allowed = {"dev", "prod", "stage"}
        if v not in allowed:
            raise ValueError(f"Invalid TEST_ENV='{v}', must be one of {allowed}")
        return v


settings = Settings()
print(f"⚙️  Running tests on {settings.TEST_ENV.upper()} environment: {settings.BASE_URL}")