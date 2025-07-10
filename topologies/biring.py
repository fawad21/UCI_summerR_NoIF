"""
biring.py – simple clockwise bidrectional ring topology for Ruby/Garnet
refrence:https://gem5bootcamp.github.io/2024/#03-Developing-gem5-models/08-ruby-network

"""

from topologies.BaseTopology import BaseTopology
from m5.objects import *


class biring(BaseTopology):
    description= "clockwise bidirectional ring"

    def __init___init_(self, controller):
        super().__init__()
        self.nodes = controllers

    def makeTopology(self, options, network, IntLink, ExtLink, Router):

        link_lat = options.link_latency
        router_lat = options.router_latency
        n = len(self.nodes)

        #Routers

        routers = [Router(router_id=i, latency=router_lat) for i in range(n)]
        network.routers = routers

        
        #  External links (controller ↔ its router)
        
        ext_links = []
        for lid, (ctrl, rtr) in enumerate(zip(self.nodes, routers)):
            ext_links.append(
                ExtLink(link_id = lid,
                        ext_node = ctrl,
                        int_node = rtr,
                        latency  = link_lat)
            )
        network.ext_links = ext_links

        
        # Internal links – clockwise + counter-clockwise
        
        int_links = []
        base = len(ext_links)

        # clockwise
        for i in range(n):
            int_links.append(
                IntLink(link_id  = base + i,
                        src_node = routers[i],
                        dst_node = routers[(i + 1) % n],
                        latency  = link_lat,
                        weight   = 1)          # weight 1
            )

        # counter-clockwise (reverse direction)
        for i in range(n):
            int_links.append(
                IntLink(link_id  = base + n + i,
                        src_node = routers[(i + 1) % n],
                        dst_node = routers[i],
                        latency  = link_lat,
                        weight   = 1)          
            )

        network.int_links = int_links
























