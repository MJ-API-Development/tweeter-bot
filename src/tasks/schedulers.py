import asyncio
import os
import re
from asyncio import Queue
from urllib.parse import urlparse
from io import BytesIO
import requests
import tweepy
import unicodedata
from pydantic import ValidationError
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


def compose_default_tweets(api_name, tweet_lines, media_ids=None):
    tweet_text = "\n".join(tweet_lines)
    tweet = {"status": f"{api_name}\n{tweet_text}"}
    if media_ids:
        tweet["media_ids"] = media_ids
    return tweet


DEFAULT_TWEETS = [
    compose_default_tweets("EOD Stock Market API", [
        "- Exchange & Ticker Data",
        "- (EOD) Stock Data",
        "- Fundamental Data",
        "- Financial News API",
        "- Social Media Trend Data For Stocks",
        "Create A free API Key today",
        "https://eod-stock-api.site/plan-descriptions/basic"
    ], media_ids=["1647575420009603073"]),
    compose_default_tweets("Financial & Business News API", [
        "- Articles By UUID",
        "- Articles By Publishing Date",
        "- Articles By Stock Tickers",
        "- Articles By Exchange",
        "- Get List of Exchanges & Tickers",
        "- Get List of Publishers & Articles By Publisher",
        "Create A free API Key today",
        "https://bit.ly/financial-business-news-api"
    ], media_ids=["1647575420009603073"]),
    compose_default_tweets("Financial & Business Professional Plan", [
        "- Exchange & Ticker Data",
        "- (EOD) Stock Data",
        "- Fundamental Data",
        "- Financial News API",
        "- Social Media Trend Data For Stocks",
        "Subscribe to our Professional Plan Today",
        "https://eod-stock-api.site/plan-descriptions/professional"
    ], media_ids=["1647575420009603073"]),
    compose_default_tweets("Financial & Business Business Plan", [
        "- Exchange & Ticker Data",
        "- (EOD) Stock Data",
        "- Fundamental Data",
        "- Financial News API",
        "- Social Media Trend Data For Stocks",
        "Subscribe to our Business Plan Today",
        "https://eod-stock-api.site/plan-descriptions/business"
    ], media_ids=["1647575420009603073"])
]


class TaskScheduler:
    def __init__(self):
        self._run_counter = 1
        self._tweepy_api = tweepy.API(auth=auth)
        self._article_queue = Queue()
        self._tweet_queue = Queue()
        self._article_count: int = 10
        self._error_delay: int = FIVE_MINUTE
        self._max_status_length: int = 250
        self._count: int = 0
        self._logger = init_logger(self.__class__.__name__)

    async def init(self):
        self._tweepy_api = tweepy.API(auth=auth)

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
            self._tweepy_api.update_status(status=tweet.get('status').strip())
            return True
        except Forbidden as e:
            self._logger.error(f"Error updating status: {str(e)}")
            self._logger.info(f"Tweet that Caused the Error : {tweet.get('status')}")
            self._tweepy_api = tweepy.API(auth=auth)
            return False

    async def do_create_tweet(self, article: ArticleData) -> dict[str, str]:
        self._logger.info("Creating Tweets")
        # Extract ticker symbols as hashtags
        if article.tickers:
            hashtags = ''.join([' #' + ticker for ticker in article.tickers])
        elif article.sentiment and article.sentiment.stock_codes:
            _codes = article.sentiment.stock_codes
            hashtags = ''.join([' #' + ticker for ticker in _codes])
        else:
            hashtags = ""

        # Create the tweet text with hashtags
        _title: str = "https://eod-stock-api.site"
        _crop_len: int = self._max_status_length - len(_title) - 6 - len(hashtags)
        tweet_body = f"{article.sentiment.article_tldr[:_crop_len]}" if article.sentiment and article.sentiment.article_tldr else article.title

        tweet_text = f"{_title}\n-{tweet_body}...\n{hashtags}"

        if article.thumbnail.resolutions:
            _url: str = article.thumbnail.resolutions[0].url
            response = requests.get(_url)
            media_content = response.content
            media_file = BytesIO(media_content)
            media = self._tweepy_api.media_upload(filename=get_filename(_url), file=media_file)

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
        if self._run_counter % 2 == 0:
            for tweet in DEFAULT_TWEETS:
                await self._tweet_queue.put(tweet)

        while self._article_queue.qsize() > 0:
            self._logger.info(f"Articles Found : {self._article_queue.qsize()}")
            article = await self._article_queue.get()
            # Create Tweet
            if article:
                try:
                    tweet: dict[str, str] = await self.do_create_tweet(article=ArticleData(**article))
                    self._logger.info(f"Tweet : {tweet}")
                    await self._tweet_queue.put(tweet)
                except ValidationError as e:
                    self._logger.error(f"Error Creating Tweet: {str(e)}")
                    pass
        self._run_counter += 1

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
            tweet_sent = await self.send_tweet(tweet=tweet)
            while not tweet_sent:
                await asyncio.sleep(delay=self._error_delay)
                tweet: dict[str, str] = await self._tweet_queue.get()
                tweet_sent = await self.send_tweet(tweet=tweet)

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
