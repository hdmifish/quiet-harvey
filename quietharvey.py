import listener
import crunch
from pymongo import MongoClient
from pymongo import errors
import json
from datetime import datetime
from bubbler import Bubbler
import matplotlib.pyplot as plt
from http.client import IncompleteRead


class QuietHarvey(object):
    class Counter:
        def __init__(self):
            self.old = 0
            self.new = 0
            self.time_in = datetime.utcnow()

    def __init__(self):
        self.counter = self.Counter()
        print("Initializing...")
        print("connecting to mongo...", end='')
        with open("config.json", "r") as fp:
            cfg = json.load(fp)
        if cfg["use_local"] is True:
            # print("\nusing local database...", end='')
            self.mongo_client = MongoClient('localhost')
        else:
            # print("\nusing remote database...", end='')
            try:
                self.mongo_client = MongoClient(cfg["uri_string"])
            except errors.InvalidURI:
                print("\033[91mFAILED\033[0m\n(uri_string points to an invalid database)\nExiting...")
                exit(1)

        print("\033[92mSUCCESS\033[0m")

        self.db = self.mongo_client.tweetstream
        self.col = self.db.harvey
        self.counter.old = self.col.tweets.count()
        self.malformed = 0
        self.tweet_max = cfg["max_tweets"]

        print("\n\nPreparing to gather \033[91m" + str(self.tweet_max - self.col.tweets.count())
              + "\033[0m more tweets to reach \033[96m" + str(self.tweet_max) + "\033[0m.")
        div = float(self.tweet_max - self.col.tweets.count()) / float(6.00)
        sec = round(div, 2)
        hr = round(float(div / 3600), 3)
        print("Popular strings tend to produce 4-8 tweets per second.\nTherefore, at this rate it should take a "
              + "popular query around \033[94m" + str(sec)
              + "\033[0m seconds (or \033[94m" + str(hr) + "\033[0m hours) for this to finish assuming a rate of "
              + "6 tweets/second")

    def error(self, status):
        if status == 401:
            print("401 UNAUTHORIZED " +
                  "(check your tokens first, but this usually happens if your system time is off by 15 minutes)")
        else:
            print("Error: " + str(status))

    def post(self, data):

        if self.col.tweets.count() < self.tweet_max:
            data = json.loads(data)

            try:
                print(str(self.col.tweets.count()))
                print(data["created_at"])
                print(data["user"]["screen_name"])
                print(data["user"]["name"])
                print(data["text"])
                print("\n\n\n\n")
            except KeyError:
                self.malformed += 1
                print("malformed tweet, ignoring...")
            else:
                self.counter.new = self.col.tweets.count() + 1
                formatted = {"text": data["text"],
                             "user": data["user"],
                             "timestamp_ms": data["timestamp_ms"],
                             "id_str": data["id_str"],
                             "is_rt": ("retweeted_status" in data)}
                if formatted["is_rt"]:
                    formatted["rt"] = {"rt_id" : data["retweeted_status"]["id_str"],
                                            "rt_text" : data["retweeted_status"]["text"],
                                            "rt_user" : data["retweeted_status"]["user"]}

                return self.col.tweets.insert(formatted)
        else:

            print("Gathering Complete! " + str(self.malformed) + " / " + str(self.col.tweets.count()) + " were malformed")

            c = crunch.Crunch(list(self.col.tweets.find()))
            c.generate_network()
            exit()
            bubble = Bubbler()

            bubble.generate_text(self.col.tweets.find(), self.col.tweets.count())
            print("Generating wordcloud...", end='')
            wordcloud = Bubbler(w=1920, h=1080, maskpath="mask.jpg").generate_cloud()
            print("DONE!")
            plt.figure()
            plt.imshow(wordcloud, interpolation="lanczos")
            plt.axis("off")
            plt.show()
            exit(0)


if __name__ == "__main__":

    client = QuietHarvey()
    try:
        listener = listener.Listener(client)
        q = "Empty"
        q = input("Please type a search phrase: ")

        client.counter.time_in = datetime.utcnow()
        while True:
            try:
                listener.run(q)
            except KeyboardInterrupt:
                raise KeyboardInterrupt
            except IncompleteRead as e:
                print("\033[91mRead Failure " + str(e) + "\033[0m")
                continue
    except KeyboardInterrupt:

        diff = client.counter.new - client.counter.old
        time_diff = (datetime.utcnow() - client.counter.time_in).total_seconds()
        rate = round(float(diff/time_diff), 2)
        print("Manually stopped. Quiet Harvey gathered \033[94m" + str(diff)
              + "\033[0m tweets containing the string: \033[91m" + q
              + "\033[0m at a rate of \033[94m" + str(rate)
              + "\033[0m tweets/second")


