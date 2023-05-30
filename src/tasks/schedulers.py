import asyncio
from asyncio import Queue

import requests
import tweepy
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


class TaskScheduler:
    def __init__(self):

        self._tweepy_api = tweepy.API(auth=auth)
        self._article_queue = Queue()
        self._tweet_queue = Queue()
        self._article_count: int = 50
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

    async def send_tweet(self, tweet):
        try:
            self._tweepy_api.update_status(status=tweet)
            return True
        except Forbidden as e:
            self._logger.error(f"Error updating status: {str(e)}")
            return False

    async def do_create_tweet(self, article: ArticleData) -> str:
        self._logger.info("Creating Tweets")
        # Extract ticker symbols as hashtags
        hashtags = ' '.join(['#' + ticker for ticker in article.tickers])
        internal_link: str = f"https://eod-stock-api.site/blog/financial-news/tweets/{article.uuid}"

        # Create the tweet text with hashtags
        tweet_text: str = f"""
            EOD Stock API - Financial & Business News
            
            {hashtags}
            - {article.title}
            
            - {article.sentiment.article_tldr[0:60]}...            
            {internal_link}
        """
        return tweet_text

        # Post the tweet

    async def create_tweets(self):
        """
            **create_tweet**
                create a tweet based on the up-coming article form a set of composed articles
                then send the tweet based on the article using send_tweet
        :return:
        """
        while self._article_queue.qsize() > 0:
            self._logger.info(f"Articles Found : {self._article_queue.qsize()}")
            article = await self._article_queue.get()
            # Create Tweet
            if article:
                tweet = await self.do_create_tweet(article=ArticleData(**article))
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

        tweet: str | None = await self._tweet_queue.get()
        if tweet:
            while tweet and not await self.send_tweet(tweet=tweet):
                await asyncio.sleep(delay=60)
                tweet: str = await self._tweet_queue.get()

        return None
