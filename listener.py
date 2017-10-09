from tweepy import Stream
from tweepy import OAuthHandler
from tweepy.streaming import StreamListener
import json

with open ("config.json", "r") as fp:
    cfg = json.load(fp)

con_key = cfg["con_key"]
con_sec = cfg["con_sec"]
tok_key = cfg["tok_key"]
tok_sec = cfg["tok_sec"]


class Listener(StreamListener):
    """
    A implementation of tweepy.StreamListener to access Twitter's Stream API
    based on a filter string
    """

    def __init__(self, client):
        """
        Constructor. Sets up the authentication handler to grant us access
        to the Twitter API
        Also handles linking the client
        :param client: quietharvey.QuietHarvey client object
        """
        self.auth = OAuthHandler(con_key, con_sec)
        self.auth.set_access_token(tok_key, tok_sec)
        self.client = client
        self.tweet_stream = self.tweet_stream = Stream(auth=self.auth,
                                                       listener=self)

    def on_data(self, data):
        """
        Called when a new Tweet is received
        :param data: JSON-formatted string representing a Tweet
        :return: True to calling function
        """
        self.client.post(data)
        return True

    def on_error(self, status):
        """
        Called when there is an error in our request to Twitter or vice versa
        :param status: int HTTP status code
        :return: None
        """
        self.client.error(status)

    def disconnect(self):
        """
        Stops and disconnects the connection to Twitter cleanly
        :return: None
        """
        self.tweet_stream.disconnect()
        print("Disconnected cleanly from Twitter")

    def run(self, tracker):
        """
        Establish connection to Twitter's Stream API
        :param tracker: str to look for in tweet
        :return: None

        :note: FUNCTION IS BLOCKING
        """
        self.tweet_stream.filter(track=[tracker])

