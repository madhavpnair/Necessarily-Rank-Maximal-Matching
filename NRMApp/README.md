# RASC-based NRMM Simulator
## Tech Stack
- FastAPI + python for backend. 
- [`Networkx`](https://networkx.org/en/) library for basic graph functions
- Developed [`graph_utils`](./implementation/lib/graph_utils.py) and [`edmonds_gallai`](./implementation/lib/edmonds_gallai.py) library modules to implement the algorithm
- JavaScript for frontend
- Websocket facilitates bi-directional (queries to agents and responses from agents) real-time communication
- In-memory dictionaries store the states
- Deployed on render

## Features
- Visualizes each step of the algorithm iteration
- Updates and renders the bipartite graph after each iteration
- Robust error handling to catch inconsistent preferences and cheating
- Real-time logging of every event
    - Query
    - Response
    - Storing future preference
    - Cache hit
    - Warnings for invalids responses
    - Edges added after each iteration
    - System logs related to connection status
- Shows the state of the in-memory dictionary which stores the future preferences to reduce query cost