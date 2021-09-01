# DPOP-algorithm-implementation

This is an implementation of DPOP algorithm in meeting scheduling problem which was a demanded work in the context of course "Intelligent Agents and Robotic Systems" of MSc in Artificial Intelligent.

## The meeting scheduling problem
In this work each problem is determined by:

- _N_ agents which are in hierarchical relationship, increasing the number of the children-nodes of each parent-node by 1 in each level, as is shown in the below image:

<img src='https://github.com/george22294/DPOP-algorithm-implementation/blob/main/examples/problem%20description/problem_hierarchy.png'>

- _M_ meetings

Every problem produced by our generator consists of almost the same number of the three different kind of meetings:

- group (GRP) meetings consisting of a node and all its children
- parent to child (PTC) meetings
- sibling (SIB) meetings

Each agent has multiple variables, each one for a meeting in which it is a participant. Every variable can be assigned with one of 8 possible values. Each of these values denotes the starting time of the meeting. 

Also, each agent has its own preferences for the starting time of the meetings as well as for the different kind of meeting (produced randomly by our generator w.r.t. the above constraint). These preferences are expressed by two _utility functions_ (the one for the starting time and the other for the kind of meeting). The _utility_ of a scheduled meeting _m_ for agent _i_ is:

_m_i_U_ = _m_i_utility_ * _s_i_utility_ 

where:
- _m_i_utility_ is the utility, regarding the meeting kind, of agent _i_ for meeting _m_
- _s_i_utility_ is the utility, regarding the starting time, of agent _i_ for time _s_ which it chose

The _overall utility_ (_i_U_) of each agent is the sum of all _m_i_U_ which it "enjoys" for every meeting it is a participant. The goal is to maximize the sum of _i_U_ for all the agents.

## Algorithm workflow - Implementation details
- At first, a problem is generated, like the one illustrated in the below image (also see the file [DCOP_Problem_20](https://github.com/george22294/DPOP-algorithm-implementation/blob/main/examples/generated%20problems/DCOP_Problem_20)):

<img src="https://github.com/george22294/DPOP-algorithm-implementation/blob/main/examples/hierarchy%20trees/hierarchy_tree_20.png">

- Based on such a problem, a constrained graph is produced:
<img src="https://github.com/george22294/DPOP-algorithm-implementation/blob/main/examples/constraints%20graphs/constraints_graph_20.png">

- Next, the pseudotree is created running a DFS search on the constrained graph:
<img src="https://github.com/george22294/DPOP-algorithm-implementation/blob/main/examples/pseudotrees/pseudotree_20.png">

- Then, taking into account the pseoudotree, the procedures of UTIL and VALUE propagation are executed until the end of the algorithm.

It should be noted that our implementation deviates from that described in DPOP original paper:

A. Petcu, B. Faltings, “DPOP: A Scalable Method for Multiagent Constraint Optimization” in Nineteenth International Joint Conference on Artificial Intelligence (IJCAI-05), July 30-August 5, 2005, Edinburgh, Scotland, UK, pp. 266-271. [Online]. Available: https://www.researchgate.net/publication/220816021_DPOP_A_Scalable_Method_for_Multiagent_Constraint_Optimization

The main difference is that we perform DFS in constraint graph, considering a macroscopic approximation of its view. We deem that with this approach we regulate and decrease the network traffic. 
Another discrepancy, which is a result of the previous one, is the way that the UTIL and VALUE propagation are carried out. We observe that in our approach, the _hybercube_ size (multi-dimensional message size) is maintained extremely low in comparison with other DPOP implementations for the same problem. The below results prove the aforementioned state: 

<img src="https://github.com/george22294/DPOP-algorithm-implementation/blob/main/results/results_plot.png">

A possible drawback of our out-of-the-box solution might be the uncertainty of the optimality of the meeting scheduling outcomes. 

For more insights about our generator and DPOP approach, please read the "DPOP_report.pdf" .

## Running the algorithm
You can find useful information 
