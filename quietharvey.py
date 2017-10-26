from __future__ import print_function
import listener
import crunch
from pymongo import MongoClient
from pymongo import errors
import json
from datetime import datetime
import time
from bubbler import Bubbler
import matplotlib.pyplot as plt
import threading
import sys
from _tkinter import TclError
import timeseries
from urllib3.exceptions import ProtocolError

def print(s, end='\n', file=sys.stdout):
    file.write(s + end)
    file.flush()


class ProgressBar(threading.Thread):
    """
    Thread class for printing the gathering progress bar
    """
    def __init__(self):
        threading.Thread.__init__(self)

    def run(self):
        func = 0.00
        bar = ""
        oldbuf = 0
        while func < 1.00 and len(client.tweet_buffer) >= 0 or client.running:

            func = float(client.tweet_count / client.tweet_max)
            buflen = len(client.tweet_buffer)

            if func < 0.05:
                bar = "=                  "
            elif func < 0.1:
                bar = "==                 "
            elif func < 0.15:
                bar = "===                "
            elif func < 0.2:
                bar = "====               "
            elif func < 0.25:
                bar = "=====              "
            elif func < 0.3:
                bar = "======             "
            elif func < 0.35:
                bar = "=======            "
            elif func < 0.4:
                bar = "========           "
            elif func < 0.45:
                bar = "=========          "
            elif func < 0.5:
                bar = "==========         "
            elif func < 0.55:
                bar = "===========        "
            elif func < 0.6:
                bar = "============       "
            elif func < 0.65:
                bar = "=============      "
            elif func < 0.7:
                bar = "==============     "
            elif func < 0.75:
                bar = "===============    "
            elif func < 0.8:
                bar = "================   "
            elif func < 0.85:
                bar = "=================  "
            elif func < 0.9:
                bar = "================== "
            elif func < 1:
                bar = "==================-"
            elif func == 1:
                bar = "-------DONE--------"

            if buflen == 0:
                bbar = "----DONE----"
            elif buflen < 100:
                bbar = "=           "
            elif func < 500:
                bbar = "==          "
            elif func < 1000:
                bbar = "===         "
            elif func < 2000:
                bbar = "====        "
            elif func < 3000:
                bbar = "=====       "
            elif func < 4000:
                bbar = "======      "
            elif func < 5000:
                bbar = "=======     "
            elif func < 6000:
                bbar = "========    "
            elif func < 7000:
                bbar = "=========   "
            elif func < 8000:
                bbar = "==========  "
            elif func < 9000:
                bbar = "=========== "
            elif func < 10000:
                bbar = "============"
            elif func > 10000:
                bbar = "==========>>"

            if oldbuf < buflen:
                arrow = ">>"
            elif oldbuf > buflen:
                arrow = "<<"
            else:
                arrow = ""

            oldbuf = buflen

            sys.stdout.write("\rProgress: [" + bar + "] {0:.0f}%".format(func * 100.00) +
                             " ({c}/{m})".format(c=client.tweet_count, m=client.tweet_max) + " "
                             "Buffer size [" + bbar  +"][" + arrow + "] ({} tweets in buffer)".format(str(buflen)))


            sys.stdout.flush()

            time.sleep(0.5)


class Worker(threading.Thread):
    """
    Thread class for asynchronously pushing tweets to the database
    """
    def __init__(self, name):
        threading.Thread.__init__(self)
        self.name = name
        print("Thread " + name + " Created!")

    def run(self):
        #
        while client.running or len(client.tweet_buffer) > 0 \
                and not client.cutoff:
            if len(client.tweet_buffer) > 0:
                data = ""
                num = ""
                data, num = client.tweet_buffer.pop()
                data = json.loads(data)
                data["val"] = str(num)

                try:
                   # print("Worker: " + self.name + " processing tweet " + data["id_str"])
                    client.counter.new = client.col.tweets.count() + 1
                    formatted = {"text": data["text"],
                                 "user": data["user"],
                                 "timestamp_ms": data["timestamp_ms"],
                                 "id_str": data["id_str"],
                                 "is_rt": ("retweeted_status" in data)}

                    if formatted["is_rt"]:
                        formatted["rt"] = {
                            "rt_id": data["retweeted_status"]["id_str"],
                            "rt_text": data["retweeted_status"]["text"],
                            "rt_user": data["retweeted_status"]["user"],
                            "rt_popularity": data['retweeted_status']['retweet_count'] + data['retweeted_status']['favorite_count'] + data['retweeted_status']['reply_count'] + data['retweeted_status']['quote_count']
                        }

                    if client.col.tweets.find({"id_str":
                                               data["id_str"]}).count() == 0:
                        client.col.tweets.insert(formatted)
                    else:
                       # print("Item already exists")
                        client.tweet_count -= 1
                    if client.col.tweets.count() >= client.tweet_max:
                        client.cutoff = True
                     #   print("Stopping all workers, cutoff reached")

                except KeyError:
                    client.malformed += 1
                    client.tweet_count -= 1
                    #print("malformed tweet, ignoring...")


class QuietHarvey(object):
    """
    Main Class for handling connections and UI
    Usage: QuietHarvey()
    """
    class Counter:
        # Used to store publicly accessible variables cleanly
        def __init__(self):
            self.old = 0
            self.new = 0
            self.time_in = datetime.utcnow()

    def __init__(self):
        """
        Class constructor, sets up config and attributes
        """

        # Way to manually stop the thread
        self.running = False
        self.mode = None
        self.query = "tweets"
        self.color = False
        self.cutoff = False

        # Create the storage class
        self.counter = self.Counter()

        print("Initializing...")
        print("Loading config.json...", end="")
        # Load the config file into a dictionary
        with open("config.json", "r") as fp:
            self.cfg = json.load(fp)

        print("DONE!")
        print("connecting to mongo...", end='')
        # Check which DB we are using
        if self.cfg["use_local"] is True:
            # print("\nusing local database...", end='')
            self.mongo_client = MongoClient('localhost')

        else:
            # print("\nusing remote database...", end='')

            # Attempt to connect to the database
            try:
                self.mongo_client = MongoClient(self.cfg["uri_string"])
            except errors.InvalidURI:
                print("\033[91mFAILED\033[0m\n " +
                      "(uri_string points to an invalid database)\nExiting...")
                exit(1)

        print("\033[92mSUCCESS\033[0m")
        # NOTE: \033[XXm codes are for changing the console color of the text
        print("Accessing \"tweetstream\" " +
              "database (If it doesn't exist, it will be created)...", end='')
        self.db = self.mongo_client.tweetstream
        print("This may take a bit...")

        # PyMongo is dynamic so you can just name a
        # collection even if it doesnt exist
        print("Acessing \"harvey\" collection " +
              "(If it doesn't exist, it will be created)...", end='')
        self.col = self.db.harvey
        print("This may take a bit...")

        print("Setting up static values [counter]...", end='')
        self.counter.old, self.tweet_count = \
            self.col.tweets.count(), self.col.tweets.count()

        # Counts the number of tweets that are missing data
        # This deals with managing connection hiccups
        self.malformed = 0
        self.thread_count = self.cfg["thread_count"]

        print("DONE!")
        print("Setting up static values [max tweets]...", end='')
        self.tweet_max = self.cfg["max_tweets"]
        print("DONE!")

        # A collection of Worker threads
        print("Setting up static values [thread_pool]...", end='')
        self.thread_pool = []
        print("DONE!")

        # A queue for buffering the input from twitter on slower systems
        print("Setting up static values [tweet_buffer]...", end='')
        self.tweet_buffer = list()
        print("DONE!")
        # Allow the listener and client objects to call each-others functions
        self.listener = None

        self.query = ""

        # Below is a visually appealing way to show the ERT
        # (Estimated Gathering Time)
        print("\n\nPreparing to gather \033[91m"
              + str(self.tweet_max - self.col.tweets.count())
              + "\033[0m more tweets to reach \033[96m"
              + str(self.tweet_max) + "\033[0m.")

        div = float(self.tweet_max - self.col.tweets.count()) / \
            float(6.00 * self.thread_count)
        sec = round(div, 2)
        hr = round(float(div / 3600), 3)

        print("Popular strings tend to be retrievable at "
              + "6-8 tweets per second per thread "
              + "\nTherefore, at this rate it should take a CPU to process a "
              + "popular query in around \033[94m" + str(sec)
              + "\033[0m seconds (or \033[94m" + str(hr)
              + "\033[0m hours) assuming a rate of "
              + str(self.thread_count * 6) + " tweets/second")

    @staticmethod
    def error(status):
        """
        Error handler. Mainly deals with explaining a 401 error
        :param status: an integer from Listener.on_error()
        :return: None
        """
        if status == 401:
            print("401 UNAUTHORIZED " +
                  "(check your tokens first, but this "
                  "usually happens if your system time is off by 15 minutes)")
        else:
            print("Error: " + str(status))

    def post(self, data):
        """
        Handles moving the data from the listener to the tweet_buffer
        :param data: a JSON-formatted string representing a single tweet
        :return: None
        """

        if self.tweet_count < self.tweet_max and not self.cutoff:
            # Keep adding tweets from twitter to the buffer as they come in
            self.tweet_count += 1
            self.tweet_buffer.append((data, self.tweet_count))

        else:
            if self.col.tweets.count() < self.tweet_max:
                return
            # When tweet_count exceeds the maximum tweets to gather
            # (set in config) disconnect from twitter
            self.listener.disconnect()
            # Tell the worker threads to stop when they finish
            # emptying the tweet_buffer to Mongo
            self.running = False

            for thread_worker in self.thread_pool:
                print("Waiting on thread: " + thread_worker.name
                      + " to finish...", end='')
                thread_worker.join()
                print("DONE!")

            print("Gathering Complete! " + str(self.malformed) + " / "
                  + str(self.col.tweets.count()) + " were malformed")
            self.analyze()

    def analyze(self):
        """
        Handles the interaction between Mongo and data crunching classes
        :return: None
        """

        if self.mode == 7:
            top_rts = list(self.col.tweets.find({}).sort([('rt.rt_popularity', -1)]).limit(10))
            all_tweets = list(self.col.tweets.find({}).sort([('timestamp_ms', 1)]))
            timeseries.generate_timeseries(all_tweets, top_rts)

        if self.mode == 6:
            print("Generating choropleth...")
            sys.stdout.flush()
            c = crunch.Crunch(list(self.col.tweets.find()), config=self.cfg)
            sys.stdout.flush()
            c.generate_choropleth()

        if self.mode in [1, 4]:
            # Initialize a Crunch object

            print("Creating Crunch Dataset...", end='')
            sys.stdout.flush()
            c = crunch.Crunch(list(self.col.tweets.find()), config=self.cfg)

            print("\nGenerating retweet frequency graph...",
                  end='')
            sys.stdout.flush()
            if c.generate_rt_frequency():
                # The above if statement just saves us from the redundency
                # of creating a graph with no data
                try:
                    c.generate_graph(xax="Account", yax="Retweets",
                                     title="Re-Tweets from Account",
                                     fig="RT data about " + self.query,
                                     mode=1)
                except TclError:
                    print("\033[31Tkinter encountered an error rendering "
                          "your graph. Is there a valid $DISPLAY variable set")
            sys.stdout.flush()

            user, val = c.get_top_tweet()
            if user is None:
                print("\033[31mMultiple Entries share frequency. "
                      "Cannot generate top tweet\033[0m")
            else:
                tweet = self.col.tweets.find_one(
                    {"rt.rt_user.id_str": str(user)})
                print("\n\n---------------------------------\nTop Retweet:"
                      + "\nUser: "
                      + tweet["rt"]["rt_user"]["screen_name"]
                      + "\nTweet: " + tweet["rt"][ "rt_text"]
                      + "\nWith " + str(val)
                      + " tweets"
                      + "\n--------------------------------------\n")
            print("\n\nGenerating tweet graph...")
            if c.generate_frequency():
                try:
                    c.generate_graph(xax="Account",
                                     yax="Tweets",
                                     title="Tweets from Account",
                                     fig="Tweet data about "
                                         + self.query, mode=0)
                except TclError:
                    print("\033[31Tkinter encountered an error rendering "
                          "your graph. Is there a valid $DISPLAY variable set")

            sys.stdout.flush()

            user, val = c.get_top_tweet()
            if user is None:
                print("\033[31mMultiple Entries share frequency."
                      " Cannot generate top tweet\033[0m")
            else:
                # print(user)
                tweet = self.col.tweets.find_one({"user.id_str" : str(user)})
                print("\n\n------------------------\nTop Tweet:"
                      "\nUser: "
                      + tweet["user"]["screen_name"]
                      + "\nTweet: " + tweet["text"]
                      + "\nWith " + str(val)
                      + " tweets\n\n-------------------------------")

        if self.mode in [2, 3, 4]:
            print("Initializing Bubbler...", end='', flush=True)
            sys.stdout.flush()
            bubble = Bubbler()
            print("DONE!", flush=True)

            # For bubbler to work we need to create a text file to read
            if self.mode != 3:
                bubble.generate_text(self.col.tweets.find(),
                                     self.col.tweets.count())
            else:
                print("Using static text file...")
            print("Generating wordcloud...", end='', flush=True)
            sys.stdout.flush()
            # we want to use a binary mask image following
            # wordcloud.py's design
            # https://github.com/amueller/word_cloud

            wc = Bubbler(w=1920, h=1080,
                                maskpath=self.cfg["mask"])
            wordcloud = wc.generate_cloud()
            print("DONE!")

            try:
                plt.figure(None, figsize=(10, 10)).canvas.set_window_title(
                    "WordCloud for " + self.query)
            except TclError as e:
                print("\033[91mTkinter couldn't generate a figure that "
                      "large. Usually this is a memory issue, shrinking.\nE: "
                      + str(e) + " \033[0m")
                return None
            else:
                if self.color:
                    plt.imshow(wc.recolor(), interpolation="lanczos")
                else:
                    plt.imshow(wordcloud, Interpolation="lanczos")
                plt.axis("off")
                plt.show()



if __name__ == "__main__":

    client = QuietHarvey()

    while True:
        # Menu Loop
        print("Quiet Harvey Main Menu")
        mode = input("\n\n[1]Crunch, [2]WordCloud, [3]WordCloud(no update), "
                     "[4]Crunch&WC  \033[33m[5]Custom Color Map ("
                     + ["\033[31moff\033[33m","\033[32mon\033[33m"]
                     [client.color] +
                     ")\033[0m [6]Choropleth/Worldmap [7]Timeseries [8]Quit\nChoose a mode: ")
        try:
            if int(mode) in [1, 2, 3, 4, 6, 7]:
                client.mode = int(mode)
                # Determine if we need to connect to twitter at all,
                # or if just need to analyze our data
                if client.tweet_max - client.col.tweets.count() > 0:
                    try:
                        # Create a Listener to handle connections with Twitter
                        # Connect the two classes
                        L = listener.Listener(client)
                        client.listener = L

                        q = "Empty"
                        q = input("Please type a search phrase: ")
                        client.query = q

                        client.counter.time_in = datetime.utcnow()

                        try:
                            # Tell threads to continue to loop
                            # even if queue is empty.
                            client.running = True
                            client.thread_pool = []
                            for t in range(client.thread_count):
                                # Create threads and start them
                                client.thread_pool.append(Worker(name=str(t)))
                                client.thread_pool[t].start()

                            # Connect to twitter and gather tweets
                            p = ProgressBar().start()
                            L.run(q)

                        except KeyboardInterrupt:
                            # For manually disconnecting
                            raise KeyboardInterrupt

                        except ProtocolError as e:
                            # A rescue statement for when tweets come too slow
                            print("\033[91mRead Failure " + str(e) + "\033[0m")

                    except KeyboardInterrupt:
                        # Manual disconnect
                        print("\033[93mGathering Stoped By User \033[0m")
                        # Step 1: Stop threads cleanly, so we don't
                        # corrupt the database or put the program in an
                        # unsafe state.
                        client.running = False
                        print("Waiting on threads to stop...")
                        for worker in client.thread_pool:
                            print("Waiting on thread: " + worker.name
                                  + " to finish...", end='')
                            worker.join()

                            print("DONE!")

                    finally:
                        # After disconnecting
                        # (either manually or automatically),
                        # calculate metrics of gathering.
                        diff = client.counter.new - client.counter.old
                        if diff > 0:
                            time_diff = \
                                (datetime.utcnow() -
                                    client.counter.time_in).total_seconds()

                            rate = round(float(diff/time_diff), 2)
                            print("Program Finished! "
                                  + "Quiet Harvey gathered \033[94m"
                                  + str(diff)
                                  + "\033[0m tweets containing the string:"
                                  + "\033[91m" + q
                                  + "\033[0m at a rate of \033[94m" + str(rate)
                                  + "\033[0m tweets/second")
                        else:
                            # If we didnt gather any tweets
                            print("Program Finished! No tweets were gathered!")

                else:
                    # Start analysis without connecting to twitter
                    print("No tweets to gather. Moving on...")
                    client.analyze()

            elif int(mode) == 5:
                client.color = not client.color
            elif int(mode) == 8:
                exit()
            else:
                print("Invalid option, please choose a valid option")
        except ValueError as e:
            print(str(e))
            print("Type a number only")
