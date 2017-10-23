import numpy as np
import matplotlib.pyplot as plt
import plotly
import plotly.plotly as py
import plotly.graph_objs as go
import plotly.offline as pyo
from datetime import datetime
import json
import pandas as pd
import sys
from dateutil import parser
from pymongo import MongoClient

def generate_timeseries():
    with open("config.json", "r") as fp:
        cfg = json.load(fp)

    db = None

    if cfg["use_local"] is True:
        # print("\nusing local database...", end='')
        db = MongoClient('localhost')
    else:
        db = MongoClient(cfg["uri_string"])

    top_rts = db.tweetstream.harvey.tweets.find({}).sort([('rt.rt_popularity', -1)]).limit(10)
    all_tweets = db.tweetstream.harvey.tweets.find({}).sort([('timestamp_ms', 1)])

    top = [r['rt']['rt_id'] for r in top_rts]

    retweets = {}
    hours = []
    print(all_tweets.count(), 'tweets')
    for tweet in all_tweets:

        if not 'rt' in tweet:
            continue

        rt_id = tweet['rt']['rt_id']

        if not rt_id in top:
            continue

        date = datetime.fromtimestamp(int(tweet['timestamp_ms'])/1000.0)

        hour = date.minute
        hour_str = str(hour)

        if not hour in hours:
            hours.append(hour)

        if not rt_id in retweets:
            retweets[rt_id] = {}
            retweets[rt_id][hour_str] = 1
        else:
            if not hour_str in retweets[rt_id]:
                retweets[rt_id][hour_str] = 1
            else:
                retweets[rt_id][hour_str] += 1

    for rt, hrs in retweets.items():
        # print(rt, hrs)
        xs = []
        ys = []

        for hr, cnt in hrs.items():
            xs.append(int(hr))
            ys.append(cnt)

        plt.plot(xs, ys)

    plt.show()