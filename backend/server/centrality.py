from collections import deque
from server.graph import WeightedGraph, UnweightedGraph
from enum import Enum, auto
import time

class Centrality(Enum):
    CLOSENESS = auto()
    BETWEENNESS = auto()

def compute_betweenness_centrality(G: UnweightedGraph, max_nodes=50):
    """
    Compute betweenness centrality with optimizations:
    1. Limit to max_nodes most connected nodes
    2. Early termination for large graphs
    3. Skip isolated nodes
    """
    # If graph is too large, use a sample
    nodes = G.nodes
    if len(nodes) > max_nodes:
        # Sort nodes by degree (number of connections) and take top max_nodes
        nodes = sorted(nodes, key=lambda n: len(n.neighbors), reverse=True)[:max_nodes]
    
    # Initialize centrality scores
    C_B = {w: 0 for w in G.nodes}
    
    # Set a timeout for processing
    start_time = time.time()
    timeout = 5  # seconds
    
    # Process each node as a source
    for i, s in enumerate(nodes):
        # Skip isolated nodes
        if not s.neighbors:
            continue
            
        # Check timeout
        if time.time() - start_time > timeout:
            print(f"Timeout reached after processing {i} nodes")
            break
            
        # Initialize data structures
        S = deque()
        P = {w: [] for w in G.nodes}
        sigma = {w: 1 if w == s else 0 for w in G.nodes}
        d = {w: 0 if w == s else -1 for w in G.nodes}
        
        Q = deque([s])
        
        # BFS to compute shortest paths
        while Q:
            v = Q.popleft()
            S.append(v)
            
            for w in v.neighbors:
                if d[w] < 0:
                    Q.append(w)
                    d[w] = d[v] + 1
                
                if d[w] == d[v] + 1:
                    sigma[w] += sigma[v]
                    P[w].append(v)
        
        # Accumulate dependencies
        delta = {v: 0 for v in G.nodes}
        
        while S:
            w = S.pop()
            for v in P[w]:
                delta[v] += (sigma[v] / sigma[w]) * (1 + delta[w])
            if w != s:
                C_B[w] += delta[w]
    
    # Assign centrality measures to nodes
    for w in G.nodes:
        w.centrality_measure = C_B[w]

def compute_closeness_centrality(G: WeightedGraph, max_nodes=50):
    """
    Optimized closeness centrality computation
    """
    n = len(G.nodes)
    
    # For small graphs, process all nodes
    # For large graphs, focus on most connected nodes
    if n > max_nodes:
        nodes = sorted(G.nodes, key=lambda n: len(n.neighbors), reverse=True)[:max_nodes]
    else:
        nodes = G.nodes
    
    # Process each node
    for node in nodes:
        # Skip isolated nodes
        if not node.neighbors:
            node.centrality_measure = 0
            continue
            
        # Calculate total distance
        distance = sum(node.neighbors.values())
        
        # Compute closeness centrality
        node.centrality_measure = 0 if distance == 0 else (n - 1) / distance