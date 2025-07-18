"""
kite.py - kite small topology for gem5 simulator
Refrence: https://ieeexplore.ieee.org/stamp/stamp.jsp?tp=&arnumber=9218539&tag=1

"""


from topologies.BaseTopology import BaseTopology
from m5.objects import *
import math

class kite(BaseTopology):
    description='Kite Small Topology'

    def __init__(self, controllers):
        super().__init__() 
        self.nodes = controllers

    def makeTopology(self, options, network, IntLink, ExtLink, Router):
        # Configuration parameters; can change latency here
        mesh_link_latency = getattr(options, 'mesh_link_latency', 4)
        express_link_latency = getattr(options, 'express_link_latency', 2)
        uc_link_latency = getattr(options, 'uc_link_latency', 2)
        router_latency = options.router_latency

        k = getattr(options, 'k_val', 12)  # Default to 8x8 for 64 nodes
        if k < 2:
            fatal("k_val must be at least 2 for Kite topology.")

        # Calculate number of routers and UCs
        num_cpu_nodes = k * k  # Total CPU nodes
        
        
        uc_positions = self._calculate_uc_positions(k)
        num_uc_routers = len(uc_positions)
        num_routers_in_network = num_cpu_nodes + num_uc_routers

        if len(self.nodes) != num_routers_in_network:
            fatal(f"Number of controllers ({len(self.nodes)}) must be equal to total routers ({num_routers_in_network}) for Kite topology with k={k}.")

        print(f"--- Creating Kite Small Topology ---")
        print(f"Grid size (k x k): {k} x {k}")
        print(f"Number of CPU nodes: {num_cpu_nodes}")
        print(f"Number of UC routers: {num_uc_routers}")
        print(f"Total nodes in network: {num_routers_in_network}")
        print(f"UC positions: {uc_positions}")

        # Create CPU routers (0 to num_cpu_nodes-1)
        cpu_routers = []
        for i in range(num_cpu_nodes):
            router = Router(router_id=i, latency=router_latency)
            cpu_routers.append(router)

        # Create UC routers (num_cpu_nodes to num_routers_in_network-1)
        uc_routers = []
        for i in range(num_uc_routers):
            router = Router(router_id=num_cpu_nodes + i, latency=router_latency)
            uc_routers.append(router)
        
        network.routers = cpu_routers + uc_routers

        # Store topology information
        self.k = k
        self.num_cpu_nodes = num_cpu_nodes
        self.num_uc_routers = num_uc_routers
        self.total_routers = num_routers_in_network
        self.uc_positions = uc_positions

        # Create adjacency matrix for routing
        self.adjacency_matrix = [[False for _ in range(num_routers_in_network)] for _ in range(num_routers_in_network)]

        link_count = 0
        ext_links = []

        # External Links (Router to Controller)
        for i, ctrl in enumerate(self.nodes):
            ext_links.append(ExtLink(link_id=link_count, ext_node=ctrl,
                                   int_node=network.routers[i],
                                   latency=options.link_latency))
            link_count += 1
        network.ext_links = ext_links

        # Internal Links
        int_links = []
        
        def add_bidir_link(src_router, dst_router, latency_val):
            nonlocal link_count
            
            src_id = src_router.router_id
            dst_id = dst_router.router_id
            
            # Update adjacency matrix
            self.adjacency_matrix[src_id][dst_id] = True
            self.adjacency_matrix[dst_id][src_id] = True
            
            # Create bidirectional links
            int_links.append(IntLink(
                link_id=link_count, 
                src_node=src_router, 
                dst_node=dst_router, 
                latency=latency_val
            ))
            link_count += 1
            
            int_links.append(IntLink(
                link_id=link_count, 
                src_node=dst_router, 
                dst_node=src_router, 
                latency=latency_val
            ))
            link_count += 1

        # Helper functions
        def get_cpu_coords(cpu_id):
            """Get (x, y) coordinates for CPU router"""
            x = cpu_id // k
            y = cpu_id % k
            return (x, y)

        def get_cpu_id(x, y):
            """Get CPU router ID from coordinates"""
            return x * k + y

        def is_valid_cpu_coord(x, y):
            """Check if coordinates are valid for CPU router"""
            return 0 <= x < k and 0 <= y < k

        # 1. Create basic mesh connections between CPU routers
        print("--- Creating CPU Mesh Links ---")
        for i in range(num_cpu_nodes):
            current_x, current_y = get_cpu_coords(i)
            src_router = cpu_routers[i]

            # Horizontal connections (East)
            if current_x + 1 < k:
                neighbor_id = get_cpu_id(current_x + 1, current_y)
                add_bidir_link(src_router, cpu_routers[neighbor_id], mesh_link_latency)

            # Vertical connections (South)
            if current_y + 1 < k:
                neighbor_id = get_cpu_id(current_x, current_y + 1)
                add_bidir_link(src_router, cpu_routers[neighbor_id], mesh_link_latency)

        # 2. Create express links (diagonal connections forming "kite" pattern)
        print("--- Creating Express Links ---")
        for i in range(num_cpu_nodes):
            current_x, current_y = get_cpu_coords(i)
            src_router = cpu_routers[i]

            # Diagonal connections (creating the "kite" pattern)
            # Main diagonal (Southeast)
            if is_valid_cpu_coord(current_x + 1, current_y + 1):
                neighbor_id = get_cpu_id(current_x + 1, current_y + 1)
                add_bidir_link(src_router, cpu_routers[neighbor_id], express_link_latency)

            # Anti-diagonal (Southwest)
            if is_valid_cpu_coord(current_x + 1, current_y - 1):
                neighbor_id = get_cpu_id(current_x + 1, current_y - 1)
                add_bidir_link(src_router, cpu_routers[neighbor_id], express_link_latency)

            # Long-range express links (every 2 hops)
            if current_x + 2 < k:
                neighbor_id = get_cpu_id(current_x + 2, current_y)
                add_bidir_link(src_router, cpu_routers[neighbor_id], express_link_latency)

            if current_y + 2 < k:
                neighbor_id = get_cpu_id(current_x, current_y + 2)
                add_bidir_link(src_router, cpu_routers[neighbor_id], express_link_latency)

        # 3. Connect UC routers to CPU routers
        print("--- Creating UC-CPU Links ---")
        for uc_idx, (uc_x, uc_y) in enumerate(uc_positions):
            uc_router = uc_routers[uc_idx]
            
            # Connect UC to surrounding CPU routers in a strategic pattern
            
            connection_radius = 2  # Connect to CPUs within radius of 2
            
            for dx in range(-connection_radius, connection_radius + 1):
                for dy in range(-connection_radius, connection_radius + 1):
                    if dx == 0 and dy == 0:
                        continue
                    
                    cpu_x = uc_x + dx
                    cpu_y = uc_y + dy
                    
                    if is_valid_cpu_coord(cpu_x, cpu_y):
                        # Connect to CPU routers with preference for strategic positions
                        distance = abs(dx) + abs(dy)  
                        if distance <= 2: 
                            cpu_id = get_cpu_id(cpu_x, cpu_y)
                            add_bidir_link(uc_router, cpu_routers[cpu_id], uc_link_latency)

        # 4. Create UC-UC express network for high-speed communication
        print("--- Creating UC-UC Express Network ---")
        for i in range(num_uc_routers):
            for j in range(i + 1, num_uc_routers):
                uc1_x, uc1_y = uc_positions[i]
                uc2_x, uc2_y = uc_positions[j]
                
                # Connect UCs if they're not too far apart
                distance = abs(uc1_x - uc2_x) + abs(uc1_y - uc2_y)
                if distance <= k // 2:  # Connect nearby UCs
                    add_bidir_link(uc_routers[i], uc_routers[j], uc_link_latency)

        network.int_links = int_links
        print(f"\nTotal internal links created: {len(int_links)}")
        print(f"Average degree per router: {len(int_links) / (2 * num_routers_in_network):.2f}")
        
        # Verify connectivity
        connectivity_ok = self._verify_connectivity()
        if not connectivity_ok:
            print("WARNING: Network connectivity issues detected!")
        
        # Calculate network diameter
        diameter = self._calculate_network_diameter()
        print(f"Network diameter: {diameter} hops")

    def _calculate_uc_positions(self, k):
        """Calculate optimal UC positions for Kite topology"""
        uc_positions = []
        
        # Strategy: Place UCs at strategic locations to maximize express connectivity
        # 1. Center regions (for hub connectivity)
        # 2. Edge midpoints (for boundary express links)
        # 3. Quarter points (for load balancing)
        
        # Place UCs at quarter points and center regions
        step = max(k // 4, 2)  # Ensure minimum spacing
        
        for i in range(1, k, step):
            for j in range(1, k, step):
                uc_positions.append((i, j))
        
        # Add edge UCs for better boundary connectivity
        mid = k // 2
        edge_positions = [
            (0, mid),      # Top edge
            (k-1, mid),    # Bottom edge  
            (mid, 0),      # Left edge
            (mid, k-1)     # Right edge
        ]
        
        for pos in edge_positions:
            if pos not in uc_positions and 0 <= pos[0] < k and 0 <= pos[1] < k:
                uc_positions.append(pos)
        
        # Add corner UCs for diagonal express links
        corner_positions = [(1, 1), (1, k-2), (k-2, 1), (k-2, k-2)]
        for pos in corner_positions:
            if pos not in uc_positions and 0 <= pos[0] < k and 0 <= pos[1] < k:
                uc_positions.append(pos)
        
        return uc_positions

    def _verify_connectivity(self):
        """Verify that all routers are connected"""
        print("--- Verifying Network Connectivity ---")
        
        n = self.total_routers
        dist = [[float('inf')] * n for _ in range(n)]
        
        # Initialize distances
        for i in range(n):
            dist[i][i] = 0
            for j in range(n):
                if self.adjacency_matrix[i][j]:
                    dist[i][j] = 1
        
        # FW algorithm
        for k in range(n):
            for i in range(n):
                for j in range(n):
                    if dist[i][k] + dist[k][j] < dist[i][j]:
                        dist[i][j] = dist[i][k] + dist[k][j]
        
        # Check for disconnected components
        disconnected_pairs = []
        for i in range(n):
            for j in range(n):
                if dist[i][j] == float('inf'):
                    disconnected_pairs.append((i, j))
        
        if disconnected_pairs:
            print(f"ERROR: Found {len(disconnected_pairs)} disconnected router pairs!")
            return False
        else:
            print("Network connectivity verified: All routers are connected!")
            return True

    def _calculate_network_diameter(self):
        """Calculate the network diameter"""
        n = self.total_routers
        dist = [[float('inf')] * n for _ in range(n)]
        
        # Initialize distances
        for i in range(n):
            dist[i][i] = 0
            for j in range(n):
                if self.adjacency_matrix[i][j]:
                    dist[i][j] = 1
        
        # FW algorithm
        for k in range(n):
            for i in range(n):
                for j in range(n):
                    if dist[i][k] + dist[k][j] < dist[i][j]:
                        dist[i][j] = dist[i][k] + dist[k][j]
        
        # Find diameter
        diameter = 0
        for i in range(n):
            for j in range(n):
                if dist[i][j] != float('inf') and dist[i][j] > diameter:
                    diameter = dist[i][j]
        
        return diameter

    def getRoutingAlgorithm(self):
        """Return the routing algorithm to use"""
        return "xy"  # XY routing works well with express links

    def registerTopology(self, options):
        """Register topology with gem5"""
        pass

    def getInterfaceVector(self, router):
        """Return interface vector for a router"""
        return []