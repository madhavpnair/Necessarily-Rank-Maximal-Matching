import networkx as nx


def create_graph(vertices, edges):
    G = nx.Graph()
    G.add_nodes_from(vertices)
    G.add_edges_from(edges)

    M = nx.algorithms.matching.max_weight_matching(G, maxcardinality=True)
    
    print("Matching:", M)


if __name__ == "__main__":
    V = {"a1","a2","a3","a4"}
    E = {("a1","a2"),("a2","a3"),("a3","a4")}
    
    print("test the create_graph function")
    create_graph(V,E)