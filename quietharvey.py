import listener
import crunch
from pymongo import MongoClient
from pymongo import errors
import json
from datetime import datetime
from bubbler import Bubbler
import matplotlib.pyplot as plt
import threading
from queue import Queue
from urllib3.exceptions import ProtocolError



class QuietHarvey(object):
    class Counter:
        def __init__(self):
            self.old = 0
            self.new = 0
            self.time_in = datetime.utcnow()



    def __init__(self):
        self.running = False
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
        self.thread = threading.Thread(target=self.worker, args=())
        self.process_buffer = list()
        self.listener = None
        self.tweet_count = self.col.tweets.count()

        self.query = ""


        print("\n\nPreparing to gather \033[91m" + str(self.tweet_max - self.col.tweets.count())
              + "\033[0m more tweets to reach \033[96m" + str(self.tweet_max) + "\033[0m.")
        div = float(self.tweet_max - self.col.tweets.count()) / float(6.00)
        sec = round(div, 2)
        hr = round(float(div / 3600), 3)
        print("Popular strings tend to produce 4-8 tweets per second.\nTherefore, at this rate it should take a "
              + "popular query around \033[94m" + str(sec)
              + "\033[0m seconds (or \033[94m" + str(hr) + "\033[0m hours) for this to finish assuming a rate of "
              + "6 tweets/second")

    def worker(self):
        while self.running or len(self.process_buffer) > 0:
            if len(self.process_buffer) > 0:

                data = json.loads(self.process_buffer.pop())

                try:
                    print(str(self.col.tweets.count()))
                    self.counter.new = self.col.tweets.count() + 1
                    formatted = {"text": data["text"],
                                 "user": data["user"],
                                 "timestamp_ms": data["timestamp_ms"],
                                 "id_str": data["id_str"],
                                 "is_rt": ("retweeted_status" in data)}
                    if formatted["is_rt"]:
                        formatted["rt"] = {"rt_id": data["retweeted_status"]["id_str"],
                                           "rt_text": data["retweeted_status"]["text"],
                                           "rt_user": data["retweeted_status"]["user"]}

                    self.col.tweets.insert(formatted)

                except KeyError:
                    self.malformed += 1
                    print("malformed tweet, ignoring...")
    def error(self, status):
        if status == 401:
            print("401 UNAUTHORIZED " +
                  "(check your tokens first, but this usually happens if your system time is off by 15 minutes)")
        else:
            print("Error: " + str(status))

    def post(self, data):

        if self.tweet_count < self.tweet_max:
            self.process_buffer.append(data)
            self.tweet_count += 1
        else:
            self.listener.disconnect()
            self.running = False
            self.thread.join()

            print("Gathering Complete! " + str(self.malformed) + " / " + str(self.col.tweets.count()) + " were malformed")
            if self.mode in [1, 3]:
                c = crunch.Crunch(list(self.col.tweets.find()))
                if c.generate_rt_frequency():
                    c.generate_graph(xax="Account", yax="Retweets", title="Re-Tweets from Account", fig="RT data about "
                                                                                                    + self.query)
                if c.generate_frequency():
                    c.generate_graph(xax="Account", yax="Tweets", title="Tweets from Account", fig="Tweet data about "
                                                                                     + self.query)
            if self.mode in [2, 3]:
                bubble = Bubbler()

                bubble.generate_text(self.col.tweets.find(), self.col.tweets.count())
                print("Generating wordcloud...", end='')
                wordcloud = Bubbler(w=1920, h=1080, maskpath="mask.jpg").generate_cloud()
                print("DONE!")
                plt.figure().canvas.set_window_title("WordCloud for " + self.query)
                plt.imshow(wordcloud, interpolation="lanczos")
                plt.axis("off")
                plt.show()
            exit(0)


if __name__ == "__main__":

    client = QuietHarvey()
    while True:
        mode = input("\n\n[1]Crunch, [2]WordCloud, [3]Both, [4]Quit\nChoose a mode: ")
        if int(mode) in [1, 2, 3]:

            try:
                listener = listener.Listener(client)
                client.listener = listener


                client.mode = int(mode)

                q = "Empty"
                q = input("Please type a search phrase: ")
                client.query = q

                client.counter.time_in = datetime.utcnow()
                while True:
                    try:
                        client.running = True
                        client.thread.start()

                        listener.run(q)
                    except KeyboardInterrupt:
                        raise KeyboardInterrupt
                    except ProtocolError as e:
                        print("\033[91mRead Failure " + str(e) + "\033[0m")
                        continue
            except KeyboardInterrupt:
                running = False
                diff = client.counter.new - client.counter.old
                time_diff = (datetime.utcnow() - client.counter.time_in).total_seconds()
                rate = round(float(diff/time_diff), 2)
                print("Manually stopped. Quiet Harvey gathered \033[94m" + str(diff)
                      + "\033[0m tweets containing the string: \033[91m" + q
                      + "\033[0m at a rate of \033[94m" + str(rate)
                      + "\033[0m tweets/second")
        elif int(mode) == 4:
            print("Goodbye")
            exit()

        else:
            print("Invalid option, please choose a valid option")

