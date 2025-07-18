"""
meshcon_noif.py - FD/UD cross connected mesh topology



Refrence: https://ieeexplore.ieee.org/stamp/stamp.jsp?tp=&arnumber=8771326
"""

from topologies.BaseTopology import BaseTopology
from m5.objects import *
import math

class meshcon_noif(BaseTopology):
    description='Scalable 2D Meshed Network of FD and UD Routers (Custom Topology)'

    def __init__(self, controllers):
        super().__init__() 
        self.nodes = controllers

    def makeTopology(self, options, network, IntLink, ExtLink, Router):

        fd_link_latency = getattr(options, 'fd_link_latency', 2)  #can change the latency here
        ud_link_latency = getattr(options, 'ud_link_latency', 4)  
        router_latency = options.router_latency 

        k = getattr(options, 'k_val', 10) # Default to 3 if not provided
        if k < 1:
            fatal("k_val must be at least 1 for this topology.")

        num_fd_routers = k * k
        num_ud_routers = (k - 1) * (k - 1) if k >= 2 else 0
        num_routers_in_network = num_fd_routers + num_ud_routers

        if len(self.nodes) != num_routers_in_network:
            fatal(f"Number of controllers ({len(self.nodes)}) must be equal to total routers ({num_routers_in_network}) for this custom topology with k={k}.")

        print(f"--- Creating Scalable 2D Meshed Network of FD and UD Routers ---")
        print(f"FD mesh side length (k) = {k}")
        print(f"Number of FD routers: {num_fd_routers}")
        print(f"Number of UD routers: {num_ud_routers}")
        print(f"Total routers in network: {num_routers_in_network}")
        print(f"Total attached controllers (nodes): {len(self.nodes)}")
        print(f"FD/UD Link Latency: {fd_link_latency} cycles")
        print(f"UD/UD Link Latency: {ud_link_latency} cycles")
        print(f"Router Latency: {router_latency} cycles")

        fd_routers = [Router(router_id=i, latency=router_latency) for i in range(num_fd_routers)]
        ud_router_start_id = num_fd_routers
        ud_routers = [Router(router_id=ud_router_start_id + i, latency=router_latency) for i in range(num_ud_routers)]
        
        network.routers = fd_routers + ud_routers

        link_count = 0
        ext_links = []


        print(f"DEBUG: k_val being used: {k}")
        print(f"DEBUG: Calculated total routers: {num_routers_in_network}")
        print(f"DEBUG: Actual nodes received: {len(self.nodes)}")


        # --- External Links (Router to Controller) ---
        for i, ctrl in enumerate(self.nodes):
            ext_links.append(ExtLink(link_id=link_count, ext_node=ctrl,
                                     int_node=network.routers[i],
                                     latency = options.link_latency)) 
            link_count += 1
        network.ext_links = ext_links
        print(f"Created {len(ext_links)} external links.")

        # --- Internal Links (Router-to-Router Connections) ---
        int_links = []
        print('\n--- Creating Internal Links ---')

        # Helper to add a bidirectional link with specified latency
        def add_bidir_link(src_router, dst_router, latency_val):
            nonlocal link_count
            int_links.append(IntLink(link_id=link_count, src_node=src_router, dst_node=dst_router, latency=latency_val, weight=1))
            link_count += 1
            int_links.append(IntLink(link_id=link_count, src_node=dst_router, dst_node=src_router, latency=latency_val, weight=1))
            link_count += 1

        # Helper to get FD router coordinates
        def get_fd_coords(fd_router_id):
            x = fd_router_id // k
            y = fd_router_id % k
            return (x, y)

        # Helper to get 1D FD router ID from 2D coordinates
        def get_fd_router_id(x, y):
            return x * k + y

        # Helper to get UD router coordinates from 1D ID (relative to start of UD routers)
        def get_ud_coords(ud_router_idx):
            ud_side_len = (k - 1) if k >= 2 else 0
            if ud_side_len == 0: return (0,0)
            ud_x = ud_router_idx // ud_side_len
            ud_y = ud_router_idx % ud_side_len
            return (ud_x, ud_y)


        # 1. FD Mesh Connections (FD-FD links)
        print("--- Creating FD-FD Links (Mesh Connections) ---")
        for i in range(num_fd_routers):
            current_x, current_y = get_fd_coords(i)
            src_router = fd_routers[i]

            if current_x + 1 < k: # Connect East
                neighbor_id = get_fd_router_id(current_x + 1, current_y)
                add_bidir_link(src_router, fd_routers[neighbor_id], fd_link_latency)

            if current_y + 1 < k: # Connect South
                neighbor_id = get_fd_router_id(current_x, current_y + 1)
                add_bidir_link(src_router, fd_routers[neighbor_id], fd_link_latency)
        
        # 2. FD-FD Spokes (Cross Connections - if k is odd and >=3)
        # This uses fd_link_latency
        if k % 2 == 1 and k >= 3:
            print("\n--- Creating FD-FD Spokes (Cross Connections) ---")
            center_router_id = (k * k) // 2
            corner_routers = [0, k - 1, (k - 1) * k, (k * k) - 1]
            for corner_id in corner_routers:
                add_bidir_link(fd_routers[corner_id], fd_routers[center_router_id], fd_link_latency)
        elif k % 2 == 0 and k >= 2:
            print(f"Skipping FD-FD Spokes for even k={k}.")
        else: # k=1
            print(f"Skipping FD-FD Spokes for k={k}.")


        # 3. Connect UD routers if they exist (i.e., k >= 2)
        if num_ud_routers > 0:
            # FD-UD links use fd_link_latency
            print("\n--- Creating FD-UD Links ---")
            for ud_idx in range(num_ud_routers):
                ud_x, ud_y = get_ud_coords(ud_idx)
                src_ud_router = ud_routers[ud_idx]

                for i in range(2): # relative row offset
                    for j in range(2): # relative col offset
                        fd_target_x = 2 * ud_x + i
                        fd_target_y = 2 * ud_y + j

                        if fd_target_x < k and fd_target_y < k:
                            target_fd_id = get_fd_router_id(fd_target_x, fd_target_y)
                            dst_fd_router = fd_routers[target_fd_id]
                            add_bidir_link(src_ud_router, dst_fd_router, fd_link_latency)

            # 4. UD-UD Mesh Connections (Horizontal & Vertical) use ud_link_latency
            print("\n--- Creating UD-UD Links (Mesh Connections) ---")
            ud_side_len = (k - 1)

            for ud_row in range(ud_side_len):
                for ud_col in range(ud_side_len):
                    src_ud_router = ud_routers[ud_row * ud_side_len + ud_col]

                    if ud_col + 1 < ud_side_len: # Connect East
                        dst_ud_router = ud_routers[ud_row * ud_side_len + (ud_col + 1)]
                        add_bidir_link(src_ud_router, dst_ud_router, ud_link_latency)

                    if ud_row + 1 < ud_side_len: # Connect South
                        dst_ud_router = ud_routers[(ud_row + 1) * ud_side_len + ud_col]
                        add_bidir_link(src_ud_router, dst_ud_router, ud_link_latency)
            
            # 5. UD-UD Diagonal Connections (use ud_link_latency
            print("\n--- Creating UD-UD Diagonal Links ---")
            for ud_row in range(ud_side_len):
                for ud_col in range(ud_side_len):
                    src_ud_router = ud_routers[ud_row * ud_side_len + ud_col]

                    if ud_row + 1 < ud_side_len and ud_col + 1 < ud_side_len: # Connect South-East
                        dst_ud_router = ud_routers[(ud_row + 1) * ud_side_len + (ud_col + 1)]
                        add_bidir_link(src_ud_router, dst_ud_router, ud_link_latency)

                    if ud_row + 1 < ud_side_len and ud_col - 1 >= 0: # Connect South-West
                        dst_ud_router = ud_routers[(ud_row + 1) * ud_side_len + (ud_col - 1)]
                        add_bidir_link(src_ud_router, dst_ud_router, ud_link_latency)
        else:
            print("Skipping UD-UD and FD-UD links as k < 2 (no UD routers defined).")

        network.int_links = int_links
        print(f"\nTotal internal links created: {len(int_links)}")