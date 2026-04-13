from fastapi import FastAPI, WebSocket
# for rendering html pages
from fastapi.responses import HTMLResponse
from implementation.lib.graph_utils import construct_bipartite_graph, compute_maximum_matching, update_graph
from implementation.lib.edmonds_gallai import compute_edmonds_gallai
from implementation.logger_config import setup_logger

app = FastAPI()

@app.get("/")
def root():
    # render index.html
    # with open("templates/index.html") as f:
    #     return HTMLResponse(f.read())
    return {"messages": "hello"}
    

logger = setup_logger(__name__)

async def NRM(websocket: WebSocket, n):
    
    N = list(f"a{i}" for i in range(1, n+1))
    A = N.copy()

    O = list(f"o{i}" for i in range(1, n+1))
    H = [O.copy() for i in range(n+1)]

    E = []
    G = construct_bipartite_graph(A, O, E) # initialize graph with no edges, to be updated after each iteration
    F = []
    D = {}
    queryCount = 0
    M = {}

    ''' 
    this dictionary will store the rank of the last preference given by each agent
    this helps to catch an agent if she says a rank equal or lesser than the latest revealed rank
    because she could have said this better rank in previous iterations but didn't
    this is not allowed since the algo expects the best choice for the user from the given list of houses at any iteration
    this means the agent is giving inconsistent/fake preferences 
    '''
    l = {} 

    '''
    n_ou keeps track of the number of odd or unreachable vertices 
    this will be useful to check the validity of input ranks
    this indirectly quantifies the possible jump in the prefernce list of the agent
    '''
    n_ou = 0

    # simple case
    if n == 2:
        # taking string input for object for user convenience like o1,o2 etc
        await websocket.send_json({"message": "Enter a1's first preference: ", "type": "question"})
        h1 = await websocket.receive_text()
        queryCount += 1
        return {"a1": h1, "a2": f"o{3 - int(h1[1:])}"}, queryCount

    for i in range(1, n+1):
        # to collect the preference edges for this iteration, to update the graph after each iteration
        Ei = [] 
        if len(A) == 0:
            await websocket.send_json({"message": "All agents are now matched. Ending algorithm.", "type": "end"})
            break
        await websocket.send_json({"message": f"iteration number : {i}", "type": "info"})

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
                # don't terminate on catching errors in input, ask the user until she gives a vaild input
                while True:
                    # taking string input for object for user convenience like o1,o2 etc
                    await websocket.send_json({"message": f"Choose best from {H[int(a[1:])]} for {a}: ", "type": "question"})
                    text = await websocket.receive_text()
                    try:
                        h, r = text.split()
                        r = int(r)
                    except Exception as e:
                        await websocket.send_json({"message": "Please send both object and rank.", "type": 'error'})
                        continue

                    # can be removed
                    # this check will not be required for the full stack version 
                    # since they select strictly from the list of available houses from the drop-down menu provided
                    if h not in H[int(a[1:])]:
                        await websocket.send_json({"message": f"{h} is not available for {a}. Please select from the given list", "type": "error"})
                        continue

                    # catch inconsistent preferences
                    # the rank of the objects chosen by an agent should be strictly increasing

                    if a not in l:  # this key a is absent in l only in the first iteration 
                        if r != 1 :
                            await websocket.send_json({"message": f"The first choice should be the first ranked object. Please try again!", "type": "error"})
                            continue
                        else :
                            l[a] = r
                            queryCount += 1
                        
                    elif r <= l[a]:
                        await websocket.send_json({"message": f"Inconsistent preference detected for agent {a} !!. \nPlease check the input and try again!.", "type": "error"})
                        continue
                    

                    # catch if the agent says an impossible rank
                    if r > n :
                        await websocket.send_json({"message":f"Only {n} objects are there. How {h} can be your {r}th preference. Please re-check", "type": "error"})
                        continue

                    # check if the agent says a greater rank when a better rank is possible - making an illegal jump in her pref list
                    elif ( (a in l) and (r > l[a] + n_ou) ) :
                        await websocket.send_json({"message": f"n_ou is {n_ou} and your latest rank is {l[a]}.", "type": "info"})
                        await websocket.send_json({"message": f"You have made an illegal jump in your preference list. You have better ranks available.\nPlease check and say the rank of your next favourite object", "type": "error"})
                        continue
                    
                    # passed all tests on validity of the input. Query next agent
                    else :
                        break
                

            if h is not None and r is not None:
                if (a, h) not in F and r == i and h in H[int(a[1:])]:
                    Ei.append((a, h)) # collect the preference edges for this iteration, to update the graph after each iteration
                    H[int(a[1:])].remove(h)

                elif r > i:
                    D[a] = (r, h)
 
        # update instead of reconstructing
        G = update_graph(G, Ei)
        await websocket.send_json({"message": f"edges added : {Ei}", "type": "info"})
        E += Ei # update E with the new edges from this iteration

        # Augment M so that it is a maximum matching in (N ∪ O, E)
        M = compute_maximum_matching(G, N)

        # Calculate the Edmond-Gallai Decomposition U, E, O for M
        # even set is unused
        even, odd, unreachable = compute_edmonds_gallai(G, M)

        n_ou = len(odd.union(unreachable))

        # If agent a ∈ N is U or O, remove a from A
        A = [a for a in A if a in even]

        # If object o ∈ O is U or O, remove o from Hi∀i ∈ [n]
        for j in range(0, len(H)):
            Hj = [o for o in H[j] if o in even]
            H[j] = Hj

        # Add any OO or OU edges to F and remove them from E
        for a, h in M.items():
            if a in N and a in odd and (h in odd or h in unreachable):
                F.append((a, h))
                if (a, h) in E:
                    E.remove((a, h))

    # works because we have try-except in init_algo
    if len(M) < n:
        await websocket.send_json({"message": "Matching is not perfect", "type": "error"})
        raise Exception("Inconsistent preference list detected !!. \nPlease check the input and try again!.")

    return M, queryCount

# to handle persistent connections
@app.websocket('/ws/nrm')
async def init_algo(websocket: WebSocket):
    await websocket.accept()

    # send and receive
    try:
        await websocket.send_json({"message": "Send n.", "type": "question"})
        n = await websocket.receive_text()
        n = int(n)
        M, queryCount = await NRM(websocket, n)
        await websocket.send_json({
            "NRM": M,
            "query count": queryCount, 
            "type": "end"
        })
    except Exception as e:
        await websocket.send_json({"message": str(e), "type": "error"})
    finally:
        await websocket.close()

@app.get("/test")
def test():
    return {"status": "alive"}
