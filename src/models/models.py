from pydantic import BaseModel, Field, validator
from typing import Optional


class TweetModel(BaseModel):
    id: str | None
    text: str = Field(required=True)


class Sentiment(BaseModel):
    article: str
    article_tldr: str
    link: str
    sentiment_article: None | str
    sentiment_title: None | str
    stock_codes: Optional[list[str]]

    @validator('stock_codes', pre=True)
    def validate_stock_codes(cls, value):
        if not value:
            raise ValueError('invalid stock codes')
        if isinstance(value, str):
            return value.split(",")
        if isinstance(value, list):
            return value

class Resolution(BaseModel):
    url: str
    width: int
    height: int
    tag: str


class Thumbnail(BaseModel):
    resolutions: list[Resolution] | None


class ArticleData(BaseModel):
    datetime_published: str | None
    link: str | None
    providerPublishTime: int | None
    publisher: str | None
    sentiment: Sentiment | None
    thumbnail: Thumbnail
    tickers: list[str] | None
    title: str
    type: str
    uuid: str
