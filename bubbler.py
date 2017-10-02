from os import path
from wordcloud import WordCloud, STOPWORDS
from PIL import Image
import numpy as np
import re

d = path.dirname(__file__)

class Bubbler(WordCloud):
    def __init__(self, w=1280, h=1024, mw=1000, maskpath=None):
        self.stopwords = set(STOPWORDS)
        if maskpath is not None:

            self.mask = np.array(Image.open(maskpath))
            super().__init__(background_color="black", width=w, height=h, stopwords=self.stopwords, max_words=mw, mask=self.mask)

        else:
            self.mask = None
            super().__init__(width=w, height=h, stopwords=self.stopwords, max_words=mw)
        return

    def generate_text(self, dbobject):
        text = ""

        for post in dbobject:
            subtext = re.sub(r"http\S+", "", post['text'])
            text += subtext.lower() + '\n'




        with open('tweets.txt', 'w') as fp:
            fp.write(text)
        return

    def generate_cloud(self, p='tweets.txt'):
        with open(p, 'r') as fp:
            text = fp.read()

        cloud = self.generate(text)
        if self.mask is not None:
            super().to_file("maskout.png")
        return cloud






