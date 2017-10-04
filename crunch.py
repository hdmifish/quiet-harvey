import numpy
import networkx


class Crunch(object):
    class Edge:
        def __init__(self, a, b):
            self.n0 = a
            self.n1 = b
            self.weight = 0

    def __init__(self, dataset=None):
        if dataset is not None:
            self.d = dataset
        else:
            self.d = None

    def generate_network(self):
        print("Processing...")
        node_list = []
        edge_list = []

        # Generate Nodes
        for post in self.d:
            if post["user"]["id"] not in node_list:
                print("Adding " + post["user"]["screen_name"] + " ({})".format(post["user"]["id_str"]))
                node_list.append(post["user"]["id"])
        # Generate Edges

        for rt in self.d:
            try:
                print("RT...", end='')
                if post["rt"]["rt_user"]["id"] in node_list:
                    print("IN")
                    edge_list.append(self.Edge(post["user"]["id"], post["rt"]["rt_user"]["id"]))
                    print(post["user"]["screen_name"] + " ---> " + post["rt"]["rt_user"]["screen_name"])
                else:
                    print("OUT")
                    print ("Adding [RT] " + post["rt"]["rt_user"]["screen_name"] + " and connecting")
                    node_list.append(post["rt"]["rt_user"]["id"])
                    edge_list.append(self.Edge(post["user"]["id"], post["rt"]["rt_user"]["id"]))

            except KeyError:
                print("post is not RT")
        print("Nodes: " + str(len(node_list)))
        print("Edges: " + str(len(edge_list)))






