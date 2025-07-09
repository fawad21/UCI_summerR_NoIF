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

        