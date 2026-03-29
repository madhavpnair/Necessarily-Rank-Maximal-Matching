import networkx as nx
from networkx.algorithms import bipartite

def construct_bipartite_graph(agents, objects, edges):
    G = nx.Graph()
    G.add_nodes_from(agents, bipartite=0)
    G.add_nodes_from(objects, bipartite=1)
    G.add_edges_from(edges)
    return G


def compute_maximum_matching(G, N):

    raw_matching = bipartite.matching.maximum_matching(G, top_nodes=N) 
    # print(raw_matching)
    # convert the maximum matching to a dictionary format for easier access
    M = {}
    for u, v in raw_matching.items():
        # print(u, v)
        if u in N:
            M[u] = v
        
    return M

# collect the preference edges into some list and update the graph after each iteration
# not needed for now, to update the graph after each iteration
def update_graph(G, new_edges):
    G.add_edges_from(new_edges)
    return G


def compute_edmonds_gallai(G, M):
    """
    Computes Edmonds-Gallai sets (E, O, U) using a level-based Alternating BFS.
    """
    # helper 
    def is_matched_edge(u, v):
        return M.get(u) == v or M.get(v) == u

    matched_agents = set(M.keys())
    matched_objects = set(M.values())
    matched_nodes = matched_agents | matched_objects
    nodes = set(G.nodes())
    free_vertices = nodes - matched_nodes
    # print("Free vertices:", free_vertices)

    E = set(free_vertices) 
    O = set()

    queue = [(v, 0) for v in free_vertices]

    while queue:
        current_node, level = queue.pop(0)
        
        for neighbor in G.neighbors(current_node):
            matched = is_matched_edge(current_node, neighbor)

            if level % 2 == 0 and not matched:
                if neighbor not in O:
                    O.add(neighbor)
                    queue.append((neighbor, level + 1))
                    # print(f"Added {neighbor} to O (odd level {level + 1}) from current node {current_node} at level {level}")
                    
     
            elif level % 2 == 1 and matched:
                if neighbor not in E:
                    E.add(neighbor)
                    queue.append((neighbor, level + 1))
                    # print(f"Added {neighbor} to E (even level {level + 1}) from current node {current_node} at level {level}")



    U = set(G.nodes()) - E - O
    
    return E, O, U

    
# driver code to test the functions
if __name__ == "__main__":
    G = nx.Graph()
    agents = {"a1", "a2", "a3", "a4"}
    objects = {"o1", "o2", "o3", "o4"}
    
    edges = [
        ("a1", "o1"), 
        ("a2", "o3"), 
        ("a3", "o2"), 
        ("a4", "o2")
    ]
    G = construct_bipartite_graph(agents, objects, edges)
    maximum_matching = compute_maximum_matching(G, agents)
    E, O, U = compute_edmonds_gallai(G, maximum_matching)
    
    print("Edges are        :", edges)
    print("Maximum Matching :", maximum_matching)
    print(f"Even Set (E)     : {E}")
    print(f"Odd Set  (O)     : {O}")
    print(f"Unreachable (U)  : {U}")





    
