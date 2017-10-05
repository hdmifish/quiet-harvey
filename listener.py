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
        self.tweetstream = None

    def on_data(self, data):
        self.client.post(data)
        return True

    def on_error(self, status):
        self.client.error(status)

    def disconnect(self):
        self.tweetStream.disconnect()
        print("Disconnected")


    def run(self, tracker):
       # t = tweepy.API(self.auth)
       # t.update_status("Test")
        self.tweetStream = Stream(auth=self.auth, listener=self)
        self.tweetStream.filter(track=[tracker])

