from tweepy import Stream
from tweepy import OAuthHandler
from tweepy.streaming import StreamListener

import json

with open("token.json", 'r') as fp:
    config = json.load(fp)

con_key = config["con_key"]
con_sec = config["con_sec"]
tok_key = config["tok_key"]
tok_sec = config["tok_sec"]


class Listener(StreamListener):
    def on_data(self, data):
        print(data)


    def on_error(self, status):
        print(status)


auth = OAuthHandler(con_key,con_sec)
auth.set_access_token(tok_key,tok_sec)

if __name__ == "__main__":
    val = input("What do you want to crawl?: ")

    tweetStream = Stream(auth, Listener())
    tweetStream.filter(track=[val])
