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

# Set this to the number of cores in your processor. (including hyper-threaded ones)
thread_count = 4


class Worker(threading.Thread):
    """
    Thread class for asynchronously pushing tweets to the database
    """
    def __init__(self, client, name):
        threading.Thread.__init__(self)
        self.name = name
        print("Thread " + name + " Created!")

    def run(self):
        #
        while client.running or len(client.tweet_buffer) > 0:
            if len(client.tweet_buffer) > 0:
                data = ""
                num = ""
                data, num = client.tweet_buffer.pop()
                data = json.loads(data)
                data["val"] = str(num)

                try:
                    print("Worker: " + self.name + " processing tweet " + data["val"])
                    client.counter.new = client.col.tweets.count() + 1
                    formatted = {"text": data["text"],
                                 "user": data["user"],
                                 "timestamp_ms": data["timestamp_ms"],
                                 "id_str": data["id_str"],
                                 "is_rt": ("retweeted_status" in data)}
                    if formatted["is_rt"]:
                        formatted["rt"] = {"rt_id": data["retweeted_status"]["id_str"],
                                           "rt_text": data["retweeted_status"]["text"],
                                           "rt_user": data["retweeted_status"]["user"]}

                    if client.col.tweets.find({"id_str": data["id_str"]}).count() == 0:
                        client.col.tweets.insert(formatted)
                    else:
                        print("Item already exists")
                except KeyError:
                    client.malformed += 1
                    client.tweet_count -= 1
                    print("malformed tweet, ignoring...")


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

        # Create the storage class
        self.counter = self.Counter()

        print("Initializing...")
        print("connecting to mongo...", end='')
        # Load the config file into a dictionary
        with open("config.json", "r") as fp:
            self.cfg = json.load(fp)

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
                print("\033[91mFAILED\033[0m\n(uri_string points to an invalid database)\nExiting...")
                exit(1)

        print("\033[92mSUCCESS\033[0m")
        # NOTE: \033[XXm codes are for changing the console color of the text

        self.db = self.mongo_client.tweetstream

        # PyMongo is dynamic so you can just name a collection even if it doesnt exist
        self.col = self.db.harvey

        self.counter.old = self.col.tweets.count()

        # Counts the number of tweets that are missing data
        # This deals with managing connection hiccups
        self.malformed = 0

        self.tweet_max = self.cfg["max_tweets"]

        # A collection of Worker threads
        self.thread_pool = []
        # A queue for buffering the input from twitter on slower systems
        self.tweet_buffer = list()

        # Allow the listener and client objects to call each-others functions
        self.listener = None

        # A counter for how many tweets are currently in the database
        self.tweet_count = self.col.tweets.count()

        self.query = ""

        # Below is a visually appealing way to show the ERT (Estimated Gathering Time)
        print("\n\nPreparing to gather \033[91m" + str(self.tweet_max - self.col.tweets.count())
              + "\033[0m more tweets to reach \033[96m" + str(self.tweet_max) + "\033[0m.")

        div = float(self.tweet_max - self.col.tweets.count()) / float(6.00 * thread_count)
        sec = round(div, 2)
        hr = round(float(div / 3600), 3)

        print("Popular strings tend to be retrievable at 6-8 tweets per second per thread "
              + "\nTherefore, at this rate it should take a CPU to process a "
              + "popular query in around \033[94m" + str(sec)
              + "\033[0m seconds (or \033[94m" + str(hr) + "\033[0m hours) assuming a rate of "
              + str(thread_count * 6) + " tweets/second")

    def error(self, status):
        """
        Error handler. Mainly deals with explaining a 401 error
        :param status: an integer from Listener.on_error()
        :return: None
        """
        if status == 401:
            print("401 UNAUTHORIZED " +
                  "(check your tokens first, but this usually happens if your system time is off by 15 minutes)")
        else:
            print("Error: " + str(status))

    def post(self, data):
        """
        Handles moving the data from the listener to the tweet_buffer
        :param data: a JSON-formatted string representing a single tweet
        :return: None
        """

        if self.tweet_count < self.tweet_max:
            # Keep adding tweets from twitter to the buffer as they come in
            self.tweet_count += 1
            self.tweet_buffer.append((data, self.tweet_count))

        else:
            # When tweet_count exceeds the maximum tweets to gather (set in config) disconnect from twitter
            self.listener.disconnect()
            # Tell the worker threads to stop when they finish emptying the tweet_buffer to Mongo
            self.running = False

            for thread_worker in self.thread_pool:
                print("Waiting on thread: " + thread_worker.name + " to finish...", end='')
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
        if self.mode in [1, 3]:
            # Initialize a Crunch object
            c = crunch.Crunch(list(self.col.tweets.find()), config=self.cfg)
            if c.generate_rt_frequency():
                # The above if statement just saves the redundency of creating a graph with no data
                c.generate_graph(xax="Account", yax="Retweets",
                                 title="Re-Tweets from Account",
                                 fig="RT data about " + self.query,
                                 mode=1)
            if c.generate_frequency():
                c.generate_graph(xax="Account", yax="Tweets", title="Tweets from Account", fig="Tweet data about "
                                                                                               + self.query, mode=0)
        if self.mode in [2, 3]:
            bubble = Bubbler()

            # For bubbler to work we need to create a text file to read
            bubble.generate_text(self.col.tweets.find(), self.col.tweets.count())
            print("Generating wordcloud...", end='')

            # we want to use a binary mask image following wordcloud.py's design
            # https://github.com/amueller/word_cloud

            wordcloud = Bubbler(w=1920, h=1080, maskpath=self.cfg["mask"]).generate_cloud()
            print("DONE!")
            # Set properties for pyplot figure
            plt.figure().canvas.set_window_title("WordCloud for " + self.query)
            plt.imshow(wordcloud, interpolation="lanczos")
            plt.axis("off")
            plt.show()


if __name__ == "__main__":

    client = QuietHarvey()

    while True:
        # Menu Loop
        print("Quiet Harvey Main Menu")
        mode = input("\n\n[1]Crunch, [2]WordCloud, [3]Both, [4]Quit\nChoose a mode: ")
        try:
            if int(mode) in [1, 2, 3]:
                client.mode = int(mode)
                # Determine if we need to connect to twitter at all, or just need to analyze
                if client.tweet_max - client.col.tweets.count() > 0:
                    try:
                        # Create a Listener to handle connections with Twitter
                        # Connect the two classes
                        listener = listener.Listener(client)
                        client.listener = listener

                        q = "Empty"
                        q = input("Please type a search phrase: ")
                        client.query = q

                        client.counter.time_in = datetime.utcnow()

                        try:
                            # Tell threads to continue to loop even if queue is empty.
                            client.running = True
                            thread_pool = []
                            for t in range(thread_count):
                                # Create threads and start them
                                client.thread_pool.append(Worker(client, name=str(t)))
                                client.thread_pool[t].start()

                            # Conenct to twitter and gather tweets
                            listener.run(q)

                        except KeyboardInterrupt:
                            # For manually disconnecting
                            raise KeyboardInterrupt

                        except ProtocolError as e:
                            # A rescue statement for when tweets come too slow
                            print("\033[91mRead Failure " + str(e) + "\033[0m")

                    except KeyboardInterrupt:
                        # Manual disconnect
                        print("\033[93mGathering Stoped By User \033[0m")
                        # Step 1: Stop threads cleanly, so we dont corrupt the database or put the program in an
                        # unsafe state.
                        client.running = False
                        print("Waiting on threads to stop...")
                        for worker in client.thread_pool:
                            print("Waiting on thread: " + worker.name + " to finish", end='')
                            worker.join()

                            print("DONE!")

                    finally:
                        # After disconnecting (either manually or automatically), calculate metrics of gathering.
                        diff = client.counter.new - client.counter.old
                        if diff > 0:
                            time_diff = (datetime.utcnow() - client.counter.time_in).total_seconds()
                            rate = round(float(diff/time_diff), 2)
                            print("Program Finished! Quiet Harvey gathered \033[94m" + str(diff)
                                  + "\033[0m tweets containing the string: \033[91m" + q
                                  + "\033[0m at a rate of \033[94m" + str(rate)
                                  + "\033[0m tweets/second")
                        else:
                            # If we didnt gather any tweets
                            print("Program Finished! No tweets were gathered!")

                else:
                    # Start analysis without connecting to twitter
                    print("No tweets to gather. Moving on...")
                    client.analyze()

            elif int(mode) == 4:
                print("Goodbye")
                exit()

            else:
                print("Invalid option, please choose a valid option")
        except ValueError:
            print("Type a number only")
