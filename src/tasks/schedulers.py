import asyncio
import os
import re
from asyncio import Queue
from urllib.parse import urlparse

import requests
import tweepy
import unicodedata
from tweepy import Forbidden

from src.config import config_instance
from src.logger import init_logger
from src.models.models import ArticleData

consumer_key = config_instance().Tweeter.consumer_key
consumer_secret = config_instance().Tweeter.consumer_secret
access_token = config_instance().Tweeter.access_token
access_token_secret = config_instance().Tweeter.access_token_secret

auth = tweepy.OAuthHandler(consumer_key, consumer_secret)
auth.set_access_token(access_token, access_token_secret)

FIVE_MINUTE = 300

DEFAULT_TWEETS: list[dict[str, str]] = [
    dict(
        status="""
            EOD Stock Market API
            
            - Exchange & Ticker Data
            - (EOD) Stock Data
            - Fundamental Data
            - Stock Options And Splits Data
            - Financial News API
            - Social Media Trend Data For Stocks
            - Sentiment Analysis for News & Social Media
            
            Create A free API Key today 
            https://eod-stock-api.site/plan-descriptions/basic
            """,
        media_ids=["1647575420009603073"]),
    dict(
        status="""
            Financial & Business News API 
    
            - Articles By UUID
            - Articles By Publishing Date
            - Articles By Stock Tickers
            - Articles By Exchange
            - Get List of Exchanges & Tickers
            - Get List of Publishers & Articles By Publisher
    
            Create A free API Key today 
            https://bit.ly/financial-business-news-api
            """,
        media_ids=["1647575420009603073"])
]


class TaskScheduler:
    def __init__(self):

        self._tweepy_api = tweepy.API(auth=auth)
        self._article_queue = Queue()
        self._tweet_queue = Queue()
        self._article_count: int = 50
        self._error_delay: int = FIVE_MINUTE
        self._logger = init_logger(self.__class__.__name__)

    async def get_articles(self):
        """
            **get_articles**
                create a list of articles that can be used to send tweets
        :return:
        """
        self._logger.info("Fetching Articles from API")
        _params: dict[str, str] = {'api_key': config_instance().EOD_API_KEY}
        articles_url: str = f"https://gateway.eod-stock-api.site/api/v1/news/articles-bounded/{self._article_count}"
        try:
            with requests.Session() as session:
                response = session.get(url=articles_url, params=_params)
                response.raise_for_status()
                if response.headers.get('Content-Type') == 'application/json':
                    return response.json()
                return None

        except Exception as e:
            self._logger.error(f"Error fetching articles : {str(e)}")
            return None

    async def send_tweet(self, tweet: dict[str, str]):
        try:
            self._tweepy_api.update_status(**tweet)
            return True
        except Forbidden as e:
            self._logger.error(f"Error updating status: {str(e)}")
            return False

    async def do_create_tweet(self, article: ArticleData) -> dict[str, str]:
        self._logger.info("Creating Tweets")
        # Extract ticker symbols as hashtags
        hashtags = ' '.join(['#' + ticker for ticker in article.tickers])
        internal_link: str = f"https://eod-stock-api.site/blog/financial-news/tweets/{article.uuid}"

        # Create the tweet text with hashtags
        tweet_text: str = f"""
            EOD Stock API - Financial & Business News
            
            {hashtags}
            - {article.title}            
              {internal_link}
        """
        if article.thumbnail.resolutions:
            _url: str = article.thumbnail.resolutions[0].url
            response = requests.get(_url)
            media_content = response.content
            media = self._tweepy_api.media_upload(filename=get_filename(_url), file=media_content)

            tweet_data = dict(status=tweet_text, media_ids=[media.media_id])
        else:
            tweet_data = dict(status=tweet_text, media_ids=["1647575420009603073"])

        return tweet_data

        # Post the tweet

    async def create_tweets(self):
        """
            **create_tweet**
                create a tweet based on the up-coming article form a set of composed articles
                then send the tweet based on the article using send_tweet
        :return:
        """
        await self._tweet_queue.put(DEFAULT_TWEETS[0])
        await self._tweet_queue.put(DEFAULT_TWEETS[1])

        while self._article_queue.qsize() > 0:
            self._logger.info(f"Articles Found : {self._article_queue.qsize()}")
            article = await self._article_queue.get()
            # Create Tweet
            if article:
                tweet: dict[str, str] = await self.do_create_tweet(article=ArticleData(**article))
                self._logger.info(f"Tweet : {tweet}")
                await self._tweet_queue.put(tweet)

    async def run(self):
        self._logger.info("Started Run")
        if self._tweet_queue.qsize() == 0:
            response: dict[str, str | dict[str, str] | int] = await self.get_articles()
            if response.get('status'):
                payload = response.get('payload', [])
                for article in payload:
                    self._logger.info(f"Article : {article}")
                    await self._article_queue.put(item=article)

            await self.create_tweets()

        tweet: dict[str, str] | None = await self._tweet_queue.get()
        if tweet:
            while tweet and not await self.send_tweet(tweet=tweet):
                await asyncio.sleep(delay=self._error_delay)
                tweet: str = await self._tweet_queue.get()

        return None


def slugify(title: str) -> str:
    """create a slug from title"""
    # Create and Normalize the slug to remove any diacritical marks or special characters
    return unicodedata.normalize('NFKD', re.sub(r'[^a-z0-9]+', '-',
                                                title.lower()).strip('-')).encode('ascii', 'ignore').decode('utf-8')


def get_filename(url) -> str:
    parsed_url = urlparse(url)
    path = parsed_url.path
    return os.path.basename(path)
