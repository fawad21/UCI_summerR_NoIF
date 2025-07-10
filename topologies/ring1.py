"""
ring.py – simple clockwise unidrectional ring topology for Ruby/Garnet
refrence:https://gem5bootcamp.github.io/2024/#03-Developing-gem5-models/08-ruby-network

"""

from topologies.BaseTopology import BaseTopology
from m5.objects import *

class ring1(BaseTopology):                       #class name is used as topology name
    description = "Clockwise N-router ring"

    def __init__(self, controllers):
        super().__init__()                      
        self.nodes = controllers                

   
    def makeTopology(self, options, network, IntLink, ExtLink, Router):

        link_latency    = options.link_latency
        router_latency  = options.router_latency
        n_routers       = len(self.nodes)       # one router per controller

        # 1) create Routers
        routers = [Router(router_id=i, latency=router_latency)
                   for i in range(n_routers)]
        network.routers = routers

        # 2) external links (ctrl ↔ its router)
        ext_links = []
        for lid, (ctrl, rtr) in enumerate(zip(self.nodes, routers)):
            ext_links.append(ExtLink(link_id=lid,
                                     ext_node=ctrl,
                                     int_node=rtr,
                                     latency=link_latency))
        network.ext_links = ext_links

        # 3) internal clockwise ring
        int_links = []
        base = len(ext_links)
        for i in range(n_routers):
            int_links.append(IntLink(link_id = base + i,
                                     src_node = routers[i],
                                     dst_node = routers[(i + 1) % n_routers],
                                     latency  = link_latency,
                                     weight   = 1))
        network.int_links = int_links
