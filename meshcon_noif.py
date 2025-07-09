"""
meshcon_noif.py - FD/UD cross connected mesh topology



Refrence: https://ieeexplore.ieee.org/stamp/stamp.jsp?tp=&arnumber=8771326
"""

from topologies.BaseTopology import BaseTopology
from m5.objects   import *

class meshcon_noif(BaseTopology):
    description="Bidirectional FD/UD cross-mesh (13 routers)"

    def __init__(self, controllers):
        super().__init__()
        assert len(controllers) == 13, "implementing only 13 controllers"
        self.nodes = controllers              

    def makeTopology(self, opts, net, IntLink, ExtLink, Router):

        link_lat   = opts.link_latency
        router_lat = opts.router_latency
        n          = len(self.nodes)

        #  routers
        routers = [Router(router_id=i, latency=router_lat) for i in range(n)]
        net.routers = routers

        # ext links
        net.ext_links = [
            ExtLink(link_id=i,
                    ext_node=ctrl,
                    int_node=routers[i],
                    latency=link_lat)
            for i, ctrl in enumerate(self.nodes)
        ]

        #  int links
        int_links = []
        next_id   = len(net.ext_links)     

        def add_bidir(a, b):
            nonlocal next_id
            int_links.append(
                IntLink(link_id = next_id,
                        src_node = routers[a],
                        dst_node = routers[b],
                        latency  = link_lat,
                        weight   = 1)
            ); next_id += 1
            int_links.append(
                IntLink(link_id = next_id,
                        src_node = routers[b],
                        dst_node = routers[a],
                        latency  = link_lat,
                        weight   = 1)
            ); next_id += 1

        # outer FD square
        for a, b in [(0,1), (1,2), (2,5), (5,8), (8,7), (7,6), (6,3), (3,0)]:
            add_bidir(a, b)

        # spokes to centre FD4 (index 4)
        for fd in [0,1,2,3,5,6,7,8]:
            add_bidir(fd, 4)

        # FD ↔ neighbouring UD links
        neighbour_pairs = [
            (0,9), (3,9),          # UD1
            (1,10), (2,10), (5,10),# UD2
            (3,11), (6,11), (7,11),# UD3
            (5,12), (8,12), (7,12) # UD4
        ]
        for a, b in neighbour_pairs:
            add_bidir(a, b)

        # UD inner square (red links)
        for a, b in [(9,10), (10,12), (12,11), (11,9)]:
            add_bidir(a, b)

        net.int_links = int_links
