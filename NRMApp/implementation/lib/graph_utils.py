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