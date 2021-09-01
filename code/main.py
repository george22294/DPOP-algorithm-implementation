import dpop
import socket
import json
import threading
import time
from pathlib import Path
import numpy as np


if __name__ == '__main__':
    IP = "127.0.0.1"
    root_IP = IP
    agents_ips = {}
    agents_ports = {}
    Port = 38001
    root_Port = Port

    """Parse file with name DCOP_Problem_N which is in the same directory"""
    p = Path('.')
    for name in p.glob('*DCOP_Problem_*'):
        f = open(name, "r")
    count = 1
    flagTime = False
    util_meet_agents = np.empty([1, 1])
    util_time_agents = np.empty([1, 1])
    num_agents = 0
    num_meetings = 0
    num_var = 0

    for line in f.readlines():

        mlist = line.split(";")

        if count == 1:
            num_agents = int(mlist[0])

            num_meetings = int(mlist[1])
            num_var = int(mlist[2])

        elif count > 1:
            if count == 2:
                util_meet_agents.resize(num_agents, num_meetings)
                util_time_agents.resize(num_agents, num_agents)
                util_meet_agents[int(mlist[0]), int(mlist[1])] = int(mlist[2])
                previous_ag = int(mlist[0])
            elif count > 2 and flagTime == False:
                if previous_ag <= int(mlist[0]):
                    util_meet_agents[int(mlist[0]), int(mlist[1])] = int(mlist[2])
                    previous_ag = int(mlist[0])
                else:
                    util_time_agents[int(mlist[0]), int(mlist[1])] = int(mlist[2])
                    flagTime = True
            else:

                util_time_agents[int(mlist[0]), int(mlist[1])] = int(mlist[2])

        count += 1
    print("The number of agents is: " + str(num_agents))
    print("The number of variables is: " + str(num_var))
    print("The number of meeting is: " + str(num_meetings))
    for i in range(num_agents):
        agents_ips[str(i)] = IP
        agents_ports[str(i)] = Port
        Port += 1

    agents_array = []
    for i in range(num_agents):
        relations = {}
        for j in range(num_meetings):
            count_meet = 1
            for h in range(num_agents):
                if i != h:
                    if int(util_meet_agents[i, j]) != 0 and int(util_meet_agents[h, j]) != 0:
                        if count_meet == 1:

                            relations[j] = [h]
                            count_meet += 1

                        else:
                            relations[j].append(h)

        x = dpop.Agent(i, agents_ips[str(i)], agents_ports[str(i)], util_meet_agents[i,], util_time_agents[i,], relations, root_IP, root_Port, num_agents, agents_ips, agents_ports)
        agents_array.append(x)
        th = threading.Thread(target=agents_array[i].start)
        th.start()

