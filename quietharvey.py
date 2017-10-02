import listener
from pymongo import MongoClient
import json
from datetime import datetime
from bubbler import Bubbler
import matplotlib.pyplot as plt

class QuietHarvey():

    def __init__(self):
        print("Initializing...")
        print("connecting to mongo...", end='')
        self.mongo = MongoClient('localhost')
        print("done!")
        self.db = self.mongo.tweetstream
        self.col = self.db.harvey
        self.malformed = 0
        self.tweetmax = 100000

    def post(self, data):
        if self.col.tweets.count() < self.tweetmax:
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

                return self.col.tweets.insert(data)
        else:
            print("Gathering Complete! " + str(self.malformed) + " / " + str(self.col.tweets.count()) + " were malformed")

            bubble = Bubbler()
            bubble.generate_text(self.col.tweets.find())
            print("Generating wordcloud...")
            wordcloud = Bubbler(w=1920, h=1080, maskpath="mask.jpg").generate_cloud()
            plt.figure()
            plt.imshow(wordcloud, interpolation="lanczos")
            plt.axis("off")
            plt.show()
            exit(0)


if __name__ == "__main__":
    client = QuietHarvey()
    print("done!")
    listener = listener.Listener(client)

    q = input("Please type a search phrase: ")

    listener.run(q)


