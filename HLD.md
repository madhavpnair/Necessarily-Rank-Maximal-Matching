# MVP

## Overview
- `n` users (agents) take part in real-time
- The users give their preferences in real time 
- Full preference list is not needed to be submitted
- Elicit the agents based on the **RASC** query prototype
- The model should be able to elicit the agents, permanently match and mark those agents and continue with others
- let `n` users input via the same dummy interface - this can later be extended to distributed sessions 

## Design
- single concurrent session for the prototype
- In-memory dictionary instead of database for state management
- WebSockets can be avoided if zero networking
- [NetworkX](https://networkx.org/documentation/stable/tutorial.html) library support for graphs<br>
eg : [maximum matching in bipartite graph](https://networkx.org/documentation/stable/reference/algorithms/generated/networkx.algorithms.bipartite.matching.maximum_matching.html)
    - create and store a graph in session memory
    - mutate the graph in each iteration 
    - no need to recreate in each iteration 