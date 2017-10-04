from os import path
from wordcloud import WordCloud, STOPWORDS
from PIL import Image
import numpy as np
import re
from sys import stdout


d = path.dirname(__file__)

class Bubbler(WordCloud):
    def __init__(self, w=1280, h=1024, mw=1000, maskpath=None):
        self.stopwords = set(STOPWORDS)
        if maskpath is not None:

            self.mask = np.array(Image.open(maskpath))
            super().__init__(background_color="black", width=w, height=h, stopwords=self.stopwords, max_words=mw, mask=self.mask)

        else:
            self.mask = None
            self.stopwords.add("rt")
            super().__init__(width=w, height=h, stopwords=self.stopwords, max_words=mw)

        return

    def generate_text(self, dbobject, total):
        text = ""

        pcount = 0
        print("Generating text file from database...")
        for post in dbobject:
            pcount += 1
            subtext = re.sub(r"http\S+", "", post['text'])
            text += subtext.lower() + '\n'
            metric = round((float(pcount / total) * 100), 1)
            stdout.write("Percentage complete: [%d%%]    " % (metric) + " (" + str(pcount) + " of " + str(total) + ")   \r")
            stdout.flush()
        stdout.write("                                                         \n")
        stdout.flush()

        print("Writing to file...", end='')
        with open('tweets.txt', 'w') as fp:
            fp.write(text)
        print("DONE!")
        return

    def generate_distribution(self, dbobject, count):
        user_metrics = {}
        words = {}

        for post in dbobject:
            name = post["user"]["screen_name"]
            id = post["user"]["id"]

            if post["user"]["id"] in user_metrics:
                user_metrics[id]["count"] += 1
            else:
                user_metrics[id] = {"name": name, "count": 0}

            for word in post["content"]:
                if word.lower() in words:
                    words[word.lower()] += 1
                else:
                    words[word.lower()] = 1

        return user_metrics, words

    def generate_cloud(self, p='tweets.txt'):
        with open(p, 'r') as fp:
            text = fp.read()

        cloud = self.generate(text)
        if self.mask is not None:
            super().to_file("maskout.png")
        return cloud






