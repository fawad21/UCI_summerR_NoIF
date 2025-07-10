"""
flattenedbutterfly.py - 2D Flattened Butterfly Topology for gem5 simulator

Refrence: https://ieeexplore.ieee.org/stamp/stamp.jsp?tp=&arnumber=4408254&tag=1

"""


from topologies.BaseTopology import BaseTopology
from m5.objects import *

class flattenedbutterfly(BaseTopology):
    description = "2d flattened Butterfly Topology"

    def __init__ (self, controllers):
        super().__init__()
        self.nodes = controllers
    
    def makeTopology(self, opts, net, IntLink, ExtLink, Router):
        link_lat = opts.link_latency
        router_lat = opts.router_latency

        