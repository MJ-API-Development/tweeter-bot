import functools

from pydantic import BaseSettings, Field


class APPSettings(BaseSettings):
    """APP Confi settings"""
    APP_NAME: str = Field(default="ESA-Tweeter-Bot")
    TITLE: str = Field(default="EOD-Stock-API - Financial Data Tweeter Bot")
    DESCRIPTION: str = Field(default="Tweeter-Bot to send EOD-Stock-API Financial Data to Tweeter for Promotional Purposes")
    VERSION: str = Field(default="1.0.0")
    TERMS: str = Field(default="https://eod-stock-api.site/terms")
    CONTACT_NAME: str = Field(default="MJ API Development")
    CONTACT_URL: str = Field(default="https://eod-stock-api.site/contact")
    CONTACT_EMAIL: str = Field(default="info@eod-stock-api.site")
    LICENSE_NAME: str = Field(default="Apache 2.0")
    LICENSE_URL: str = Field(default="https://www.apache.org/licenses/LICENSE-2.0.html")
    DOCS_URL: str = Field(default='/docs')
    OPENAPI_URL: str = Field(default='/openapi')
    REDOC_URL: str = Field(default='/redoc')


class TweeterSettings(BaseSettings):
    pass


class Settings(BaseSettings):
    APP_SETTINGS: APPSettings = APPSettings()


@functools.lru_cache(maxsize=1)
def config_instance() -> Settings:
    return Settings()
