from fastapi import FastAPI, WebSocket
# for rendering html pages
from fastapi.responses import HTMLResponse
from implementation.lib.graph_utils import construct_bipartite_graph, compute_maximum_matching, update_graph
from implementation.lib.edmonds_gallai import compute_edmonds_gallai
from implementation.logger_config import setup_logger

from fastapi import FastAPI, Request
from fastapi.templating import Jinja2Templates

app = FastAPI()
templates = Jinja2Templates(directory="templates")

@app.get("/")
async def root(request: Request):
    # Explicitly define request= and name= to avoid the versioning bug
    return templates.TemplateResponse(
        request=request, 
        name="index.html"
    )
    

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

    # Keep track of the rank at which an edge was added to calculate the signature later
    edge_ranks = {}

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

 

    for i in range(1, n+1):
        # to collect the preference edges for this iteration, to update the graph after each iteration
        Ei = [] 
        if len(A) == 0:
            await websocket.send_json({"message": "All agents are matched. Obtained NRM.", "type": "success"})
            break
        await websocket.send_json({"message": f"iteration number : {i}", "type": "info"})

        # Broadcast all active agents and their options at the start of the iteration
        active_menus = [{"agent": a, "options": H[int(a[1:])]} for a in A]
        await websocket.send_json({"type": "iter_start", "iteration": i, "menus": active_menus})

        for a in A:
            skip = False
            h = None
            r = None
            if a in D.keys():
                retrievedRank, retrievedObj = D[a]
                if retrievedRank > i:
                    skip = True
                    # Notify frontend that the agent is skipped
                    await websocket.send_json({"message": f"Saved the query to Agent {a} (waiting for iteration {retrievedRank + 1})", "type": "skip", "skipped_agent": a})
                elif i == retrievedRank:
                    h = retrievedObj
                    r = retrievedRank
                    skip = True
                    del D[a]
                    # Notify frontend that the agent is auto-processed and update dictionary
                    await websocket.send_json({"message": f"Fetch {a}'s stored choice from dictionary: {h} (Rank {r})", "type": "cache hit", "auto_process": {"agent": a, "object": h, "rank": r}})
                    await websocket.send_json({"type": "dict_update", "dictionary": D})

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
                        await websocket.send_json({"message": "Please send both object and rank.", "type": 'warning'})
                        continue
                    
                    # n = 2 case
                    if(n==2):
                        h1 = h
                        a="a2"
                        await websocket.send_json({"message": f"Choose best from {H[int(a[1:])]} for {a}: ", "type": "question"})
                        text = await websocket.receive_text()
                        try:
                            h2, r = text.split()
                            r = int(r)
                        except Exception as e:
                            await websocket.send_json({"message": "Please send both object and rank.", "type": 'warning'})
                            continue
                        if(h1==h2):
                            sig = [1,1]
                        else:
                            sig = [2,0]

                        G = update_graph(G,[("a1",h1),("a2", h2)])
                        M = {"a1":h1, "a2":h2}
                        graph_payload = serialize_graph_state(G, M, [], [], [])

                        await websocket.send_json({
                            "type": "graph_update",
                            "iteration": 1,
                            "graph": graph_payload,
                            "message": f"Graph updated for iteration {1}"
                        })
                        await websocket.send_json({"message": "All agents are matched. Obtained NRM.", "type": "success"})
                        return {"a1": h, "a2": f"o{3 - int(h[1:])}"}, 2, sig

                    
                    # error handlings starts here
                    # ---------------------------------------

                    # this check can be removed
                    # this check will not be required for the full stack version 
                    # since they select strictly from the list of available houses from the drop-down menu provided
                    if h not in H[int(a[1:])]:
                        await websocket.send_json({"message": f"{h} is not available for {a}. Please select from the given list", "type": "warning"})
                        continue

                    # catch inconsistent preferences
                    # the rank of the objects chosen by an agent should be strictly increasing

                    if a not in l:  # this key a is absent in l only in the first iteration 
                        if r != 1 :
                            await websocket.send_json({"message": f"The first choice should be the first ranked object. Please try again!", "type": 'warning'})
                            continue
                        else :
                            l[a] = r
                            queryCount += 1
                        
                    elif r <= l[a]:
                        await websocket.send_json({"message": f"Inconsistent preference detected for agent {a} !!. \nPlease check the input and try again!.", "type": 'warning'})
                        continue

                    

                    # catch if the agent says an impossible rank
                    if r > n :
                        await websocket.send_json({"message":f"Only {n} objects are there. How {h} can be your {r}th preference. Please re-check", "type": 'warning'})
                        continue

                    # check if the agent says a greater rank when a better rank is possible - making an illegal jump in her pref list
                    elif ( (a in l) and (r > l[a] + n_ou) ) :
                        await websocket.send_json({"message": f"n_ou is {n_ou} and your latest rank is {l[a]}.", "type": "info"})
                        await websocket.send_json({"message": f"You have made an illegal jump in your preference list. You have better ranks available.\nPlease check and say the rank of your next favourite object", "type": 'warning'})
                        continue
                    
                    # passed all tests on validity of the input. Query next agent
                    else :
                        # added update
                        if r != 1:
                            l[a] = r
                            queryCount += 1
                        break
                

            if h is not None and r is not None:
                if (a, h) not in F and r == i and h in H[int(a[1:])]:
                    Ei.append((a, h)) # collect the preference edges for this iteration, to update the graph after each iteration
                    edge_ranks[(a, h)] = i # NEW: Keep track of the rank for the signature!
                    H[int(a[1:])].remove(h)

                elif r > i:
                    D[a] = (r, h)
                    # Notify frontend of dictionary update
                    await websocket.send_json({"message": f"Cached future preference for {a}: {h} at rank {r}", "type": "info"})
                    await websocket.send_json({"type": "dict_update", "dictionary": D})
 
        # update instead of reconstructing
        G = update_graph(G, Ei)
        await websocket.send_json({"message": f"edges added : {Ei}", "type": "info"})
        E += Ei # update E with the new edges from this iteration

        # Augment M so that it is a maximum matching in (N ∪ O, E)
        M = compute_maximum_matching(G, N)

        # Calculate the Edmond-Gallai Decomposition U, E, O for M
        even, odd, unreachable = compute_edmonds_gallai(G, M)

        
        # Emit the intermediate graph state to the frontend
        graph_payload = serialize_graph_state(G, M, even, odd, unreachable)
        await websocket.send_json({
            "type": "graph_update",
            "iteration": i,
            "graph": graph_payload,
            "message": f"Graph updated for iteration {i}"
        })

        # total number of inactive objects and agents
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
        await websocket.send_json({"message": "Matching is not perfect", "type": 'warning'})
        raise Exception("Inconsistent preference list detected !!. \nPlease check the input and try again!.")
    
    # Calculate Signature
    signature_counts = {}
    max_r = 0
    for a, h in M.items():
        r = edge_ranks.get((a, h), 1)
        signature_counts[r] = signature_counts.get(r, 0) + 1
        if r > max_r: 
            max_r = r
    
    # Format as list: e.g. [num_rank_1, num_rank_2, ...]
    signature_list = [signature_counts.get(k, 0) for k in range(1, max_r + 1)]
    #pad with zeroes to format signature
    x = len(signature_list);
    y = n - x
    signature_list += [0] * y

    # Clear Dictionary when done
    await websocket.send_json({"type": "dict_update", "dictionary": {}})

    return M, queryCount, signature_list



# to handle persistent connections
@app.websocket('/ws/nrm')
async def init_algo(websocket: WebSocket):
    await websocket.accept()

    # send and receive
    try:
        await websocket.send_json({"message": "Send n.", "type": "question"})
        n = await websocket.receive_text()
        n = int(n)
        M, queryCount, signature = await NRM(websocket, n)
        await websocket.send_json({
            "NRM": M,
            "query count": queryCount, 
            "signature": signature,
            "type": "end"
        })
    except Exception as e:
        await websocket.send_json({"message": str(e), "type": 'warning'})
    finally:
        await websocket.close()

def serialize_graph_state(G, M, even, odd, unreachable):
    """Converts the NetworkX graph and algorithm state into a JSON-serializable format."""
    nodes = []
    # Assumes G.nodes() returns the list of active agents and objects
    for node in G.nodes():
        # Determine the Edmond-Gallai state for frontend color-coding
        if node in even:
            state = "even" # e.g., Color Green
        elif node in odd:
            state = "odd"  # e.g., Color Red
        elif node in unreachable:
            state = "unreachable" # e.g., Color Gray
        else:
            state = "unassigned"

        nodes.append({
            "id": str(node),
            "type": "agent" if str(node).startswith("a") else "object",
            "state": state
        })

    edges = []
    for u, v in G.edges():
        # Check if this edge is part of the current maximum matching M
        is_matched = (M.get(u) == v) or (M.get(v) == u)
        edges.append({
            "source": str(u),
            "target": str(v),
            "is_matched": is_matched # Frontend can make these lines thicker/colored
        })

    return {"nodes": nodes, "edges": edges}