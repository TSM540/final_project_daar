from collections import deque
from server.graph import WeightedGraph, UnweightedGraph
from enum import Enum, auto
import time
from django.core.cache import cache

class Centrality(Enum):
    CLOSENESS = auto()
    BETWEENNESS = auto()

def compute_betweenness_centrality(G: UnweightedGraph):
    """Compute betweenness centrality with optimizations and timeout"""
    start_time = time.time()
    max_time = 2.0  # 2 second timeout
    
    # For large graphs, process only a subset of nodes
    nodes_to_process = G.nodes
    if len(G.nodes) > 30:
        # Sort nodes by connectivity and process most connected first
        nodes_to_process = sorted(G.nodes, key=lambda n: len(n.neighbors), reverse=True)[:30]
    
    C_B = {w: 0 for w in G.nodes}
    nodes_processed = 0
    
    for s in nodes_to_process:
        # Skip isolated nodes - they don't contribute to betweenness
        if not s.neighbors:
            continue
            
        # Check timeout every few nodes
        nodes_processed += 1
        if nodes_processed % 5 == 0 and time.time() - start_time > max_time:
            print(f"Betweenness calculation timeout after {nodes_processed} nodes")
            break
            
        S = deque()
        P = dict()
        sigma = dict()
        d = dict()
        
        for w in G.nodes:
            if w == s:
                sigma[w] = 1
                d[w] = 0
            else:
                sigma[w] = 0
                d[w] = -1
            P[w] = []
        
        Q = deque()
        Q.append(s)
        
        while len(Q) != 0:
            v = Q.popleft()
            S.append(v)
            
            # For nodes with many neighbors, limit processing
            neighbors_to_process = v.neighbors
            if len(v.neighbors) > 20:
                neighbors_to_process = v.neighbors[:20]
                
            for w in neighbors_to_process:
                if d[w] < 0:
                    Q.append(w)
                    d[w] = d[v] + 1
                
                if d[w] == d[v] + 1:
                    sigma[w] = sigma[w] + sigma[v]
                    P[w].append(v)
        
        delta = {v: 0 for v in G.nodes}
        
        while len(S) != 0:
            w = S.pop()
            for v in P[w]:
                delta[v] += (sigma[v] / sigma[w]) * (1 + delta[w])
            if w != s:
                C_B[w] += delta[w]
    
    print(f"Betweenness centrality calculation completed in {time.time() - start_time:.4f} seconds")
    # Assign centrality measures to nodes
    for w in G.nodes:
        w.centrality_measure = C_B[w]
    

def compute_closeness_centrality(G: WeightedGraph):
    """Optimized closeness centrality calculation with early termination for large graphs"""
    start_time = time.time()
    
    n = len(G.nodes)
    for node in G.nodes:
        # Skip isolated nodes
        if not node.neighbors:
            node.centrality_measure = 0
            continue
            
        # For nodes with many connections, approximate using subset
        if len(node.neighbors) > 20:
            # Take 20 most important connections (lowest weight = closest)
            top_neighbors = dict(sorted(node.neighbors.items(), key=lambda x: x[1])[:20])
            distance = sum(top_neighbors.values())
            # Scale distance proportionally to account for missing connections
            scaling_factor = len(node.neighbors) / len(top_neighbors)
            distance = distance * scaling_factor
        else:
            distance = sum(node.neighbors.values())
            
        # Compute closeness centrality
        node.centrality_measure = 0 if distance == 0 else (n - 1) / distance
    
    print(f"Closeness centrality calculation completed in {time.time() - start_time:.4f} seconds")