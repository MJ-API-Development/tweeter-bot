from pydantic import BaseModel, Field


class TweetModel(BaseModel):
    id: str | None
    text: str = Field(required=True)


