from pydantic import BaseModel, Field


class TweetModel(BaseModel):
    id: str | None
    text: str = Field(required=True)


class Sentiment(BaseModel):
    article: str
    article_tldr: str
    link: str
    sentiment_article: str | None
    sentiment_title: str | None
    stock_codes: list[str] | None


class Resolution(BaseModel):
    url: str
    width: int
    height: int
    tag: str


class Thumbnail(BaseModel):
    resolutions: list[Resolution]


class ArticleData(BaseModel):
    datetime_published: str
    link: str
    providerPublishTime: int
    publisher: str
    sentiment: Sentiment
    thumbnail: Thumbnail
    tickers: list[str] | None
    title: str
    type: str
    uuid: str
