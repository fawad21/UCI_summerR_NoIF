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

          # a) FD-to-FD local mesh connections (3x3 grid)
        # Horizontal links
        for row_start_idx in [0, 3, 6]: # For rows starting at FD1(0), FD4(3), FD7(6)
            for col_offset in range(2): # Connect (0,1), (1,2) for each row
                add_bidir(row_start_idx + col_offset, row_start_idx + col_offset + 1)
                print(f"FD-FD H link: R{row_start_idx + col_offset} <-> R{row_start_idx + col_offset + 1}")

        # Vertical links
        for col_start_idx in [0, 1, 2]: # For columns starting at FD1(0), FD2(1), FD3(2)
            for row_offset in range(2): # Connect (0,3), (3,6) for each column
                add_bidir(col_start_idx + (row_offset * 3), col_start_idx + ((row_offset + 1) * 3))
                print(f"FD-FD V link: R{col_start_idx + (row_offset * 3)} <-> R{col_start_idx + ((row_offset + 1) * 3)}")

       
        add_bidir(0, 4); print(f"FD-FD Spokes: R0 <-> R4") # FD1 <-> FD5
        add_bidir(2, 4); print(f"FD-FD Spokes: R2 <-> R4") # FD3 <-> FD5
        add_bidir(6, 4); print(f"FD-FD Spokes: R6 <-> R4") # FD7 <-> FD5
        add_bidir(8, 4); print(f"FD-FD Spokes: R8 <-> R4") # FD9 <-> FD5


        # c) FD <-> neighbouring UD links (black lines between FD and UD)
        print("\n--- Creating FD-UD Links ---")
        # UD1 (router 9) connects to FD1(0), FD2(1), FD4(3), FD5(4)
        add_bidir(0, 9); print(f"FD-UD Link: R0 <-> R9 (FD1-UD1)")
        add_bidir(1, 9); print(f"FD-UD Link: R1 <-> R9 (FD2-UD1)")
        add_bidir(3, 9); print(f"FD-UD Link: R3 <-> R9 (FD4-UD1)")
        add_bidir(4, 9); print(f"FD-UD Link: R4 <-> R9 (FD5-UD1)")

        # UD2 (router 10) connects to FD2(1), FD3(2), FD5(4), FD6(5)
        add_bidir(1, 10); print(f"FD-UD Link: R1 <-> R10 (FD2-UD2)")
        add_bidir(2, 10); print(f"FD-UD Link: R2 <-> R10 (FD3-UD2)")
        add_bidir(4, 10); print(f"FD-UD Link: R4 <-> R10 (FD5-UD2)")
        add_bidir(5, 10); print(f"FD-UD Link: R5 <-> R10 (FD6-UD2)")

        # UD3 (router 11) connects to FD4(3), FD5(4), FD7(6), FD8(7)
        add_bidir(3, 11); print(f"FD-UD Link: R3 <-> R11 (FD4-UD3)")
        add_bidir(4, 11); print(f"FD-UD Link: R4 <-> R11 (FD5-UD3)")
        add_bidir(6, 11); print(f"FD-UD Link: R6 <-> R11 (FD7-UD3)")
        add_bidir(7, 11); print(f"FD-UD Link: R7 <-> R11 (FD8-UD3)")

        # UD4 (router 12) connects to FD5(4), FD6(5), FD8(7), FD9(8)
        add_bidir(4, 12); print(f"FD-UD Link: R4 <-> R12 (FD5-UD4)")
        add_bidir(5, 12); print(f"FD-UD Link: R5 <-> R12 (FD6-UD4)")
        add_bidir(7, 12); print(f"FD-UD Link: R7 <-> R12 (FD8-UD4)")
        add_bidir(8, 12); print(f"FD-UD Link: R8 <-> R12 (FD9-UD4)")

        # d) UD inner square (red links)
        print("\n--- Creating UD-UD Links ---")
        add_bidir(9, 10); print(f"UD-UD Link: R9 <-> R10 (UD1-UD2)")
        add_bidir(10, 12); print(f"UD-UD Link: R10 <-> R12 (UD2-UD4)")
        add_bidir(12, 11); print(f"UD-UD Link: R12 <-> R11 (UD4-UD3)")
        add_bidir(11, 9); print(f"UD-UD Link: R11 <-> R9 (UD3-UD1)")

        net.int_links = int_links
        print(f"\nTotal internal links created: {len(int_links)}")