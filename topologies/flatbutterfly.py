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

        num_rows = opts.mesh_rows
        if num_rows <= 0:
            # Default to a square arrangement if mesh_rows is not provided or invalid.
            num_rows = int(opts.num_cpus**0.5)
            if num_rows * num_rows != opts.num_cpus:
                raise Exception("For Flattened Butterfly, num_cpus (%d) must be a perfect square, "
                                "or mesh_rows must be specified and divide num_cpus evenly." % opts.num_cpus)

        # Calculate number of columns
        num_routers = opts.num_cpus 
        if num_routers % num_rows != 0:
            raise Exception("num_cpus (%d) must be divisible by num_rows (%d) for FlattenedButterfly" % (num_routers, num_rows))
        num_columns = num_routers // num_rows

        print(f"--- Creating Flattened Butterfly Topology ---")
        print(f"Grid Dimensions: {num_rows} rows x {num_columns} columns")
        print(f"Total Routers: {num_routers}")
        

        # Create routers
        routers = [Router(router_id=i, latency=router_lat) for i in range(num_routers)]
        net.routers = routers

        
        cpu_controllers = self.nodes[0:opts.num_cpus]
        dir_controllers = self.nodes[opts.num_cpus : opts.num_cpus + opts.num_dirs]

        # Assert that the number of CPUs matches the router count (1 CPU per router)
        assert opts.num_cpus == num_routers, \
               f"FlattenedButterfly topology expects --num-cpus to equal number of routers ({num_routers}), but got {opts.num_cpus}."

        # External links 
        ext_links = []
        current_link_id = 0

        print("\n--- External Links (CPU/Directory to Router) ---")
        # Connect CPU controllers (1 CPU per router)
        for i in range(num_routers):
            ext_links.append(
                ExtLink(link_id=current_link_id,
                        ext_node=cpu_controllers[i],
                        int_node=routers[i],
                        latency=link_lat)
            )
          
                
            current_link_id += 1

        
        if opts.num_dirs > 0:
            assert opts.num_dirs == num_routers, \
                   f"FlattenedButterfly topology expects --num-dirs to equal number of routers ({num_routers}) if directories are connected, but got {opts.num_dirs}."

            for i in range(num_routers):
                ext_links.append(
                    ExtLink(link_id=current_link_id,
                            ext_node=dir_controllers[i],
                            int_node=routers[i],
                            latency=link_lat)
                )
                
                
                current_link_id += 1

        net.ext_links = ext_links

        # Internal links (inter-router connections)
        int_links = []
        next_int_link_id = current_link_id
        added_link_pairs = set() 

        # Helper to get router ID from (row, col)
        def get_router_id(r, c):
            return r * num_columns + c

        # Helper to add a bidirectional link with specified weights
        def add_bidirectional_link(router_a_id, router_b_id, weight):
            nonlocal next_int_link_id
            link_pair = tuple(sorted((router_a_id, router_b_id)))
            if link_pair not in added_link_pairs:
                # Link A to B
                int_links.append(
                    IntLink(link_id=next_int_link_id,
                            src_node=routers[router_a_id],
                            dst_node=routers[router_b_id],
                            latency=link_lat,
                            weight=weight)
                )
                
                next_int_link_id += 1

                # Link B to A (bidirectional)
                int_links.append(
                    IntLink(link_id=next_int_link_id,
                            src_node=routers[router_b_id],
                            dst_node=routers[router_a_id],
                            latency=link_lat,
                            weight=weight)
                )
                
                next_int_link_id += 1
                added_link_pairs.add(link_pair)

        
        # Create connections for each router
        for row in range(num_rows):
            for col in range(num_columns):
                current_router_id = get_router_id(row, col)

                # Dimension 1 (Horizontal) connections: +1, +2, +3 neighbors (wraps around)
                # These typically correspond to X-links, weight=1
                # +1 neighbor
                target_col_p1 = (col + 1) % num_columns
                router_id_h1 = get_router_id(row, target_col_p1)
                add_bidirectional_link(current_router_id, router_id_h1, weight=1)

                # +2 neighbor
                target_col_p2 = (col + 2) % num_columns
                router_id_h2 = get_router_id(row, target_col_p2)
                add_bidirectional_link(current_router_id, router_id_h2, weight=1)

                # +3 neighbor (or equivalent to -1 for a 4-node dimension, forming a complete graph in that dimension)
                target_col_p3 = (col + 3) % num_columns
                router_id_h3 = get_router_id(row, target_col_p3)
                add_bidirectional_link(current_router_id, router_id_h3, weight=1)


                # Dimension 2 (Vertical) connections: +1, +2, +3 neighbors (wraps around)
                # These typically correspond to Y-links, weight=2
                # +1 neighbor
                target_row_p1 = (row + 1) % num_rows
                router_id_v1 = get_router_id(target_row_p1, col)
                add_bidirectional_link(current_router_id, router_id_v1, weight=2)

                # +2 neighbor
                target_row_p2 = (row + 2) % num_rows
                router_id_v2 = get_router_id(target_row_p2, col)
                add_bidirectional_link(current_router_id, router_id_v2, weight=2)

                # +3 neighbor (or equivalent to -1 for a 4-node dimension)
                target_row_p3 = (row + 3) % num_rows
                router_id_v3 = get_router_id(target_row_p3, col)
                add_bidirectional_link(current_router_id, router_id_v3, weight=2)

        net.int_links = int_links
       