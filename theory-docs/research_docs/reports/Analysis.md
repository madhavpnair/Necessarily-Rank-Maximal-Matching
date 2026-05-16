## Literature Survey of Analysis of Jannik Peters
- The competitive ratio analysis of online elicitation of NRM matching based on **next-best** query model
- The task is to come up with such a constant ratio for the **RASC** model based NRM original algorithm

## Analysis of RASC Algorithm - Plan
- Agent-specific approach
- Compare the query cost of OPT vs. ALG for any agent `a`
- Try to impose a lower bound constraint on number of queries of `OPT` w.r.t `ALG `
- Try to get some constant difference 
    eg: `OPT >= ALG - c` (c is some constsnt)
- This directly helps to get us a constant competitive ratio