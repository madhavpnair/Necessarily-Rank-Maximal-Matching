# helper 
def is_matched_edge(M, u, v):
    return M.get(u) == v or M.get(v) == u

def compute_edmonds_gallai(G, M):
    """
    Computes Edmonds-Gallai sets (E, O, U) using a level-based Alternating BFS.
    """

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
            matched = is_matched_edge(M, current_node, neighbor)

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