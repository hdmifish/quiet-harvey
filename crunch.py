import numpy as np
import matplotlib.pyplot as plt

# TODO: Remove all debug texts that are unecessary

class Crunch(object):

    def __init__(self, dataset=None):
        if dataset is not None:
            self.d = dataset
        else:
            self.d = None

        self.frequency = {}

    def get_user_by_id(self, id):
        for post in self.d:
            if post["user"]["id"] == id:
                return post["user"]

    def get_rt_user_by_id(self, id):
        for post in self.d:
            if "rt" in post:
                if post["rt"]["rt_user"]["id"] == id:
                    return post["rt"]["rt_user"]

    def generate_frequency(self):

        self.frequency = {}
        print("Processing...")
        for post in self.d:
            if post["user"]["id"] not in self.frequency:
                self.frequency[post["user"]["id"]] = 1
            else:
                self.frequency[post["user"]["id"]] += 1

        average = float(len(self.d) / len(self.frequency))
        print("Total Items: " + str(len(self.frequency)))

        temp = {}
        for uid in self.frequency:
            if self.frequency[uid] < average:
                temp[uid] = self.frequency[uid]

        for i in temp:
            del self.frequency[i]
        print(str(self.frequency))
        if len(self.frequency) < 1:
            return False
        return True


    def generate_rt_frequency(self):
        self.frequency = {}
        print("Processing...")

        # Generate Nodes

        for post in self.d:
            if "rt" in post:
                if post["rt"]["rt_user"]["id"] not in self.frequency:
                    self.frequency[post["rt"]["rt_user"]["id"]] = 1
                else:
                    self.frequency[post["rt"]["rt_user"]["id"]] += 1

        average = float(len(self.d) / len(self.frequency))
        print("Total Items: " + str(len(self.frequency)))

        temp = {}
        for uid in self.frequency:
            if self.frequency[uid] < average:
               temp[uid] = self.frequency[uid]

        for i in temp:
            del self.frequency[i]
        print("Total Items with more than one RT: " + str(len(self.frequency)))
        if len(self.frequency) < 1:
            return False
        return True


    def generate_graph(self,
                       xax="X-Axis",
                       yax="Y-Axis",
                       title="Title",
                       fig="title"):
        bars = []
        freq = []
        average = float(len(self.d)/len(self.frequency))

        for uid in self.frequency:

            if self.frequency[uid] >= average:
                print(str(uid) + " has " + str(self.frequency[uid]))
                bars.append(self.get_rt_user_by_id(uid)["screen_name"])
                freq.append(self.frequency[uid])
        if len(bars) < 2:
            print("\033[31m Error, not enough data to construct a meaningful graph. "
                  "Higher sample size needed \033[0m")
            return False

        y_pos = np.arange(len(bars))
        plt.bar(y_pos, freq, align='center', alpha=0.5)
        plt.xticks(y_pos, bars)
        plt.xlabel("Account")
        plt.ylabel('# of Retweets')
        plt.title('Retweets by Account')
        plt.figure(num=1).canvas.set_window_title(fig)


        plt.show()





