import functools

from pydantic import BaseSettings, Field


class APPSettings(BaseSettings):
    """APP Confi settings"""
    APP_NAME: str = Field(default="ESA-Tweeter-Bot")
    TITLE: str = Field(default="EOD-Stock-API - Financial Data Tweeter Bot")
    DESCRIPTION: str = Field(
        default="Tweeter-Bot to send EOD-Stock-API Financial Data to Tweeter for Promotional Purposes")
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


class Logging(BaseSettings):
    filename: str = Field(default="financial_news.logs")

    class Config:
        env_file = '.env.development'
        env_file_encoding = 'utf-8'


class TweeterSettings(BaseSettings):

    consumer_key: str = Field(..., env="TWITTER_API_KEY")
    consumer_secret: str = Field(..., env="TWITTER_API_SECRET")
    access_token: str = Field(..., env="TWITTER_ACCESS_TOKEN")
    access_token_secret: str = Field(..., env="TWITTER_ACCESS_TOKEN_SECRET")

    class Config:
        env_file = '.env.development'
        env_file_encoding = 'utf-8'


class Settings(BaseSettings):
    EOD_API_KEY: str = Field(..., env='EOD_STOCK_API_KEY')
    DEVELOPMENT_SERVER_NAME: str = Field(..., env='DEVELOPMENT_SERVER_NAME')
    APP_SETTINGS: APPSettings = APPSettings()
    LOGGING: Logging = Logging()
    Tweeter: TweeterSettings = TweeterSettings()

    class Config:
        env_file = '.env.development'
        env_file_encoding = 'utf-8'


@functools.lru_cache(maxsize=1)
def config_instance() -> Settings:
    return Settings()
