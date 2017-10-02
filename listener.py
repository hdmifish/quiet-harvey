from tweepy import Stream
from tweepy import OAuthHandler
import tweepy
from tweepy.streaming import StreamListener
import json

with open ("config.json", "r") as fp:
    cfg = json.load(fp)

con_key = cfg["con_key"]
con_sec = cfg["con_sec"]
tok_key = cfg["tok_key"]
tok_sec = cfg["tok_sec"]



class Listener(StreamListener):

    def __init__(self, client):
        self.auth = OAuthHandler(con_key, con_sec)
        self.auth.set_access_token(tok_key, tok_sec)
        self.client = client

    def on_data(self, data):
        self.client.post(data)
        return True

    def on_error(self, status):
        self.client.error(status)

    def run(self, tracker):
       # t = tweepy.API(self.auth)
       # t.update_status("Test")
        tweetStream = Stream(auth=self.auth, listener=self)
        tweetStream.filter(track=[tracker])

