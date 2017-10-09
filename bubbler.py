from wordcloud import WordCloud, STOPWORDS
from PIL import Image
import numpy as np
import re
from sys import stdout


class Bubbler(WordCloud):
    """
    A word cloud / distribution generator that implements the WordCloud module

    """
    def __init__(self, w=1280, h=1024, mw=1000, maskpath=None):
        self.stopwords = set(STOPWORDS)
        # Stopwords are words we don't want to see in a wordcloud
        if maskpath is not None:

            # if image has a template
            self.mask = np.array(Image.open(maskpath))

            # Initialize the WordCloud object
            super().__init__(background_color="black",
                             width=w, height=h, stopwords=self.stopwords,
                             max_words=mw, mask=self.mask)
        else:
            self.mask = None
            # print(str(self.stopwords))
            super().__init__(width=w, height=h,
                             stopwords=self.stopwords, max_words=mw)
        return

    def to_html(self):
        return super().to_html()

    @staticmethod
    def generate_text(dbobject, total):
        """
        Create a human-friendly text file from all of the tweets
        :param dbobject: a cursor or list of tweets
        :param total: the total number of objects in
                      the list (cursors do not provide this themselves)
        :return: None
        """
        text = ""

        pcount = 0
        print("Generating text file from database...", flush=True)

        for post in dbobject:
            # Iterate through the database
            pcount += 1

            # Remove all unnecessary links from the file
            subtext = re.sub(r"http\S+", "", post['text'])

            # Remove RT from the text file
            text += subtext.lower().replace("rt", '').strip() + '\n'

            # Percent counter
            metric = round((float(pcount / total) * 100), 1)
            stdout.write("Percentage complete: [%d%%]    " % metric
                         + " (" + str(pcount) + " of " + str(total) + ")   \r")
            stdout.flush()

        stdout.write("                                                     \n")
        stdout.flush()

        print("Writing to file...", end='')
        with open('tweets.txt', 'w') as fp:
            fp.write(text)

        print("DONE!")
        return

    @staticmethod
    def generate_distribution(dbobject, count):
        """
        Generate two frequency maps, one of users and another of words
        :param dbobject: a cursor or list of tweets
        :param count: the total number of objects in the list
                      (cursors do not provide this themselves)
        :return: dict, dict
        """
        user_metrics = {}
        words = {}

        for post in dbobject:
            name = post["user"]["screen_name"]
            uid = post["user"]["id"]

            if post["user"]["id"] in user_metrics:
                user_metrics[uid]["count"] += 1
            else:
                user_metrics[uid] = {"name": name, "count": 0}

            for word in post["content"]:
                if word.lower() in words:
                    words[word.lower()] += 1
                else:
                    words[word.lower()] = 1

        return user_metrics, words

    def generate_cloud(self, p='tweets.txt'):
        """
        Generate the actual wordcloud from the text file
        :param p: name of text file to source words from
        :return: pyplot compatible image
        """
        with open(p, 'r') as fp:
            text = fp.read()

        # Generate wordcloud
        cloud = self.generate(text)
        if self.mask is not None:
            super().to_file("maskout.png")
        return cloud






