import networkx as nx
import tests.algo_sandbox as al

def findNRM(n):

    N = list(f"a{i}" for i in range(1, n+1))
    A = N.copy()

    O = list(f"o{i}" for i in range(1, n+1))
    H = [O.copy() for i in range(n+1)]

    E = []
    M = al.construct_bipartite_graph(A, O, E)
    F = []
    D = {}

    queryCount = 0

    # this is because we cant del current queried obj from H
    # This is the set passed to the query
    querySet = [Hi.copy() for Hi in H]

    # simple case
    if n == 2:
        h1 = int(input("Enter a1's preference: "))
        return [["a1", f"o{h1}"], ["a2", f"o{3 - h1}"]]
    
    for i in range(1, n+1):
        for a in A:
            skip = False
            h = None
            r = None
            if a in D.keys():
                retrievedRank, retrievedObj = D[a]
                if retrievedRank > i:
                    skip = True
                elif i == retrievedRank:
                    h = retrievedObj
                    r = retrievedRank
                    skip = True
                    del D[a]

            if skip == False:
                h, r = map(int, input(f"Choose best from {querySet[int(a[1])]} for {a}: ").split())
                h = f"o{h}"
                querySet[int(a[1])].remove(h)
                queryCount += 1

            if h is not None and r is not None:
                if (a, h) not in F and r == i and h in H[int(a[1])]:
                    E.append((a, h))
                    H[int(a[1])].remove(h)

                elif r > i:
                    D[a] = (r, h)
 
        # actually Gi
        G = al.construct_bipartite_graph(N, O, E)

        # Augment M so that it is a maximum matching in (N ∪ O, E)
        M = al.compute_maximum_matching(G, N)

        # Calculate the Edmond-Gallai Decomposition U, E, O for M
        even, odd, unreachable = al.compute_edmonds_gallai(G, M)

        # If agent a ∈ N is U or O, remove a from A
        A = [a for a in A if a not in odd and a not in unreachable]

        # If object o ∈ O is U or O, remove o from Hi∀i ∈ [n]
        for j in range(0, len(H)):
            Hj = [o for o in H[j] if o not in unreachable and o not in odd]
            H[j] = Hj
            querySetj = [o for o in querySet[j] if o in H[j]]
            querySet[j] = querySetj

        # Add any OO or OU edges to F and remove them from E
        for a, h in M.items():
            if a in N and a in odd and (h in odd or h in unreachable):
                F.append((a, h))
                if (a, h) in E:
                    E.remove((a, h))

    return M, queryCount

n = int(input("Enter no of agent-obj pairs: "))
print("input format: <obj_id> <obj_rank>")
M, queryCount = findNRM(n)
print("NRM: ", M)
print(f"{queryCount} queries asked.")