from __future__ import print_function
import numpy as np
import matplotlib.pyplot as plt
import plotly
import plotly.plotly as py
import plotly.offline as pyo

import json
import pandas as pd
import sys

def print(s, end='\n', file=sys.stdout):
    file.write(s + end)
    file.flush()


class Crunch(object):
    """
    An analytics handler for quiet-harvey
    :Author: John Shell
    """
    def __init__(self, data_set=None, config=None):
        """
        Constructor. Creates local copy of MongoDB collection to work with
        :param data_set: cursor or list of Tweets
        """

        if data_set is not None:
            print("Creating dataset...")
            self.d = data_set
        else:
            self.d = None

        if config is None:
            self.default_pop = 10
        else:
            self.config = config
            self.default_pop = config["target_graph_population"]
            try:
                self.ptoken = config["plotly_api_key"]
            except KeyError:
                print("Warn: No plotly token, cannot use choropleths")
        self.frequency = {}

    def get_user_by_id(self, uid):
        """
        Find non-retweeted user
        :param uid: int64 or str twitter user id
        :return: dict representing user or None
        """
        for post in self.d:
            if str(post["user"]["id"]) == str(uid):
                return post["user"]

    def get_rt_user_by_id(self, id):
        """
        Find retweeted user
        :param uid: int64 or str twitter user id
        :return: dict representing user or None
        """
        for post in self.d:
            if "rt" in post:
                if str(post["rt"]["rt_user"]["id"]) == str(id):
                    return post["rt"]["rt_user"]

    def generate_frequency(self, pop=10):
        """
        Generates a frequency of tweets/user from the database
        :return: boolean (enough data to construct a graph was generated)
        """

        # Clear the previous frequency table
        self.frequency = {}
        pop = self.default_pop
        print("Processing...")

        # Iterate through the database and populate the user table
        for post in self.d:
            if post["user"]["id"] not in self.frequency:
                self.frequency[post["user"]["id"]] = 1
            else:
                self.frequency[post["user"]["id"]] += 1

        average = float(len(self.d) / len(self.frequency))
        print("Total Items: " + str(len(self.frequency)))

        # Remove statistically "insignificant" users from frequency map
        temp = {}
        for uid in self.frequency:
            if self.frequency[uid] < average:
                temp[uid] = self.frequency[uid]

        for i in temp:
            del self.frequency[i]

        # Exponentially reduce (if applicable)
        # the number of accounts to create a meaningful graph
        # Target number can be set in config under "target_graph_population"

        while len(self.frequency) > pop:

            average = float(len(self.d) / len(self.frequency))
            print("Total Items: " + str(len(self.frequency)))

            # Copy of the data if the reduction is too severe
            rollback_dict = {}
            rollback_dict.update(self.frequency)
            temp = {}

            # Reduce
            for uid in self.frequency:
                if self.frequency[uid] < average:
                    temp[uid] = self.frequency[uid]

            for i in temp:
                del self.frequency[i]

            print("Total Items with more than " + str(average)
                  + " RT(s): " + str(len(self.frequency)))

            # Identify if loop is necessary
            if len(self.frequency) > pop:
                print("Focusing on average")

            # Rollback to previous reduction
            elif len(self.frequency) < 3:
                print("Rolling back")
                if len(rollback_dict) > pop:
                    self.frequency = {}

                    # Order dictionary by value to pick $pop
                    # number of users for the graph
                    s = [(k, rollback_dict[k])
                         for k in sorted(rollback_dict,
                                         key=rollback_dict.get, reverse=True)]
                    for k, v in s:
                        self.frequency[k] = v
                        if len(self.frequency) >= pop:
                            break

                    print("Data was compressed to " + str(pop) + " entries")
                    return True

                self.frequency.update(rollback_dict)

                return True

        if len(self.frequency) < 1:
            return False
        return True

    def generate_rt_frequency(self, pop=10):
        """
       Generates a frequency of retweets/user from the database
       :return: boolean (enough data to construct a graph was generated)
       """
        self.frequency = {}
        print("Processing...")
        pop = self.default_pop

        # Iterate through the database and populate the user table
        for post in self.d:
            if "rt" in post:
                if post["rt"]["rt_user"]["id"] not in self.frequency:
                    self.frequency[post["rt"]["rt_user"]["id"]] = 1
                else:
                    self.frequency[post["rt"]["rt_user"]["id"]] += 1

        # Remove statistically insignificant users
        average = float(len(self.d) / len(self.frequency))
        print("Total Items: " + str(len(self.frequency)))

        temp = {}
        for uid in self.frequency:
            if self.frequency[uid] < average:
                temp[uid] = self.frequency[uid]

        for i in temp:
            del self.frequency[i]

        # Exponentially reduce (if applicable) the number of accounts
        # to create a meaningful graph
        # Target number can be set in config under "target_graph_population"

        while len(self.frequency) > pop:
            average = float(len(self.d) / len(self.frequency))
            print("Total Items: " + str(len(self.frequency)))
            rollback_dict = {}
            rollback_dict.update(self.frequency)
            temp = {}

            # Reduce
            for uid in self.frequency:
                if self.frequency[uid] < average:
                    temp[uid] = self.frequency[uid]

            for i in temp:
                del self.frequency[i]

            print("Total Items with more than " + str(average) + " 1RT(s): "
                  + str(len(self.frequency)))

            # Identify is loop is necessary
            if len(self.frequency) > pop:
                print("Focusing on average")

            # Rollback to previous reduction
            elif len(self.frequency) < 3:
                print("Rolling back")
                # print(self.frequency)
                # print(rollback_dict)
                self.frequency.update(rollback_dict)
                # print(self.frequency)
                # print(str(len(self.frequency)))
                if len(rollback_dict) > pop:
                    self.frequency = {}
                    # Order dictionary by value to pick $pop number of
                    # users for the graph
                    s = [(k, rollback_dict[k])
                         for k in sorted(rollback_dict,
                                         key=rollback_dict.get,
                                         reverse=True)]
                    for k, v in s:
                        self.frequency[k] = v
                        if len(self.frequency) >= 8:
                            break
                    print("Compressed data")
                    return True
                self.frequency.update(rollback_dict)

                return True

        if len(self.frequency) < 1:
            return False

    def get_top_tweet(self):
        top = ("", 0)

        for t in self.frequency:
            if self.frequency[t] > top[1]:
                top = (t, self.frequency[t])

            if self.frequency == top[1]:
                return None, None

        return top

    def generate_graph(self,
                       xax="X-Axis",
                       yax="Y-Axis",
                       title="Title",
                       fig="title", mode=1):
        """
        Creats a pyplot bar graph showing number of tweets/retweets
        by top accounts
        :param xax: label for x-axis
        :param yax: label for y-axis
        :param title: graph title
        :param fig: figure title (for the window)
        :param mode: 0 - tweets, 1 - retweets
        :return: None
        """

        bars = []
        freq = []
        average = float(len(self.d)/len(self.frequency))

        # From the previously calculated top users (regular or retweets)
        # add them as x-axis values for bars
        for uid in self.frequency:

            # print(str(uid) + " has " + str(self.frequency[uid]))
            if mode == 1:
                bars.append(self.get_rt_user_by_id(uid)["screen_name"])
            if mode == 0:
                bars.append(self.get_user_by_id(uid)["screen_name"])
            freq.append(self.frequency[uid])

        # If we were unable to generate enough bars to make a meaningful graph
        if len(bars) < 3:
            print("\033[31m Error, not enough data to construct a"
                  " meaningful graph. "
                  "Higher sample size needed \033[0m")
            return False

        # Generate the bars
        y_pos = np.arange(len(bars))
        plt.bar(y_pos, freq, align='center', alpha=0.5)
        plt.xticks(y_pos, bars)
        plt.xlabel("Account")
        plt.ylabel('# of Retweets')
        plt.title('Retweets by Account')
        plt.figure(num=1).canvas.set_window_title(fig)
        plt.show()

    def generate_choropleth(self):
        sys.stdout.flush()
        print("Removing null location tweets...")
        sys.stdout.flush()
        temp = []
        for tweet in self.d:
            if not tweet["user"]["location"] is None:
                temp.append(tweet)
        with open("state_codes.json", "r") as fp:
            scodes = json.load(fp)

        diff = len(self.d) - len(temp)

        print("Usable tweets: " + str(diff))
        if diff < 1:
            print("\033[31mUnable to continue, not enough data! \033[0m")
            return
        sys.stdout.flush()
        locmap = {}
        error = 0
        for tweet in temp:
            loc = tweet["user"]["location"].lower().split(',')
            for state in scodes:
                for word in loc:
                    if state.lower() == word.strip() or scodes[state].lower() == word.strip():
                        # print("Matched word: " + word.strip() + " to " + state.lower())
                        if state in locmap:
                            locmap[state] += 1
                        else:
                            locmap[state] = 1

        figmap = {"state":list(locmap.keys()), "tweets":list(locmap.values())}

        df = pd.DataFrame.from_dict(figmap, orient="columns")

        for col in df.columns:
            df[col] = df[col].astype(str)

        scl = [[0.0, 'rgb(240,245,247)'], [0.2, 'rgb(217,230,235)'], [0.4, 'rgb(188,211,220)'], \
               [0.6, 'rgb(154,187,200)'], [0.8, 'rgb(107,157,177)'], [1.0, 'rgb(39,114,143)']]

        df['text'] = df['state'] + '<br>' + "Tweets: " + df['tweets']

        data = [dict(
            type='choropleth',
            colorscale=scl,
            autocolorscale=False,
            locations=df['state'],
            z=df['tweets'].astype(float),
            locationmode='USA-states',
            marker=dict(
                line=dict(
                    color='rgb(255,255,255)',
                    width=2
                )),
            colorbar=dict(
                title="Tweets")
        )]

        layout = dict(
            title="Tweet Distribution by State (from " + str(diff) + " tweets)",

            geo=dict(
                scope='usa',
                projection=dict(type='albers usa'),
                showlakes=True,
                lakecolor='rgb(255, 255, 255)'),
        )

        fig = dict(data=data, layout=layout)
        if self.config["plotly_api_key"] != "":
            print("attempting to plot online....")
            plotly.tools.set_credentials_file(username=self.config["plotly_api_user"], api_key=self.config["plotly_api_key"])
            py.iplot(fig, filename='Tweets By State')

        pyo.plot(fig, auto_open=True, image='png', image_filename="harvey_choropleth",
                     output_type='file', image_width=1920, image_height=1080, filename="harvey_choropleth.html")

        return True

