import socket
import json
import threading
import time
from pathlib import Path
import numpy as np
import udp
import pygraphviz as pgv
import sys

def binary_combinations(number):
    if number > 2:
        comb = factor(number) / (factor(2) * factor(number - 2))
        return comb
    elif 2 >= number >= 0:
        return number

def factor(number):
    if number == 0:
        fact = 1
        return fact
    elif 2 >= number > 0:
        return number
    elif number > 2:
        fact = 1
        for i in range(2, number+1):
            fact = fact * i
        return fact

def dfs(dict_nod_meet, current_node_id, parent_id, pseudtree, visited):
    if current_node_id not in visited:
        if parent_id == "None":
            pseudtree[current_node_id] = []
            visited[current_node_id] = True
        elif parent_id in pseudtree:

            pseudtree[parent_id].append(current_node_id)
            visited[current_node_id] = True
        else:
            pseudtree[parent_id] = [current_node_id]
            visited[current_node_id] = True

        for node_in_same_meet in dict_nod_meet[current_node_id]:

            dfs(dict_nod_meet, str(node_in_same_meet), current_node_id, pseudtree, visited)

    return pseudtree

class Agent:

    def __init__(self, ID, IP, Port, util_meet, util_time, relations, root_IP, root_Port, num_agents, agents_ips, agents_ports):
        self.id = ID
        self.IP = IP
        self.Port = Port
        self.utility_meet = {}
        self.utility_time = {}
        self.relations = relations
        self.msgs = {}
        self.root_IP = root_IP
        self.root_Port = root_Port
        self.only_root_know_list_agents = []
        self.neighbors = self.find_neighbors()
        self.num_agents = num_agents
        self.agents_ips = agents_ips
        self.agents_ports = agents_ports
        self.pseudo_parents = []
        self.pseudo_children = []
        self.real_parents = []
        self.real_children = []
        self.domain = []
        self.combined_utilities = {}
        self.size_of_message = 0
        self.p_pp_domains = {}
        self.p_pp_util_time = {}
        self.p_pp_util_meet = {}
        for util in range(len(util_meet)):
            if util_meet[util] != 0:
                self.utility_meet[str(util)] = util_meet[util]
        for util in range(len(util_time)):
            if util_time[util] != 0:
                self.utility_time[str(util)] = util_time[util]
                self.domain.append(util)


    def find_neighbors(self):

        neig_list = []
        for meet in self.relations.keys():
            cur_list = []
            cur_list = self.relations[meet]
            for memb in cur_list:
                memb_flag = False
                for mem in neig_list:
                    if mem == memb:
                        memb_flag = True
                if not memb_flag:
                    neig_list.append(memb)
        return neig_list



    def start(self):


        msgs = self.msgs
        Ip = self.IP
        Port = self.Port


        Listen = threading.Thread(name='Listening-Thread-of-Agent-'+str(self.id), target=udp.receive_udp_mes, args=(msgs, Ip, Port))
        Listen.start()


        if self.Port == self.root_Port:

            """Pseudotree creation"""

            """Root is waiting for the message with the neighbors of all other nodes to begin the DFS search"""

            print("Root is agent: " + str(self.id) + ". He is waiting for all agents to send him their neighbors.")
            time.sleep(5)

            while True:

                time.sleep(2)
                countMes = 0
                for mes in msgs:
                    countMes += 1
                print(countMes)
                if countMes == (self.num_agents-1):
                    print("All agents has sent to root their neighbors and he begins the creation of pseudotree.")
                    break

            dict_nod_w_meet_nod = {str(self.id): self.neighbors}
            dict_for_constraints = {str(self.id): self.relations}

            for mes in msgs:
                mes_msgs = msgs[mes]
                if len(mes_msgs["neighbors"]) != 0:

                    dict_nod_w_meet_nod[mes[13:]] = mes_msgs["neighbors"]
                    dict_for_constraints[mes[13:]] = mes_msgs["relations"]
                    self.only_root_know_list_agents.append(mes[13:])
                else:
                    print("There is agent with ID: " + str(mes[13:]) + " who is not participating in any meeting!")

            """Find the number of binary constraints"""

            """The number of total exclusion restrictions is the sum of exclusion restrictions of each agent. The exclusion restrictions of each agent is all the possible combinations of his different meetings-variables"""
            all_meets = {}
            exclusion_restrictions = 0
            for ag in dict_for_constraints:
                meets_num = len(dict_for_constraints[ag])
                exclusion_restrictions += int(binary_combinations(meets_num))
                for met in dict_for_constraints[ag]:
                    if met not in all_meets:
                        met_dict_for_constraints = dict_for_constraints[ag]
                        all_meets[met] = len(met_dict_for_constraints[met]) + 1
            print("Total exclusion restrictions are: " + str(exclusion_restrictions))

            """The number of equality restrictions is the sum of the number of all possible combinations of agents in each meeting"""
            equality_restrictions = 0
            for met in all_meets:
                equality_restrictions += int(binary_combinations(all_meets[met]))
            print("Total equality restrictions are: " + str(equality_restrictions))
            print("Total number of constraints are: " + str(equality_restrictions + exclusion_restrictions))

            pseudotree = {}
            visited = {}

            """DFS search"""
            pseudotree = dfs(dict_nod_w_meet_nod, str(self.id), "None", {}, visited)
            """Some nodes have to be added as leaves"""
            for node in dict_nod_w_meet_nod:
                if node not in pseudotree:
                    pseudotree[node] = []

            """Get parents of every node in pseudotree"""
            parents = {str(self.id): "None"}
            for node in pseudotree:
                for child in pseudotree[node]:
                    parents[child] = node


            """Some nodes formed unconnected trees because they are interlinked only among them."""
            """Find them and connect their pseudotree as a child with the node which have the least links """
            extra_pseudotree = {}
            countExtra = 0
            for node in pseudotree:

                if node not in parents:
                    print("There are unconnected graphs!")
                    countExtra += 1
                    extra_pseudotree[str(countExtra)] = dfs(dict_nod_w_meet_nod, node, "None", {}, {})
                    countChil = -1
                    best_node = None
                    for node_again in pseudotree:

                        if countChil == -1 and (node_again in parents):
                            countChil = len(pseudotree[node_again])
                            best_node = node_again

                        elif countChil > len(pseudotree[node_again]) and (node_again in parents):
                            countChil = len(pseudotree[node_again])
                            best_node = node_again
                    pseudotree[best_node].append(node)
                    parents[node] = best_node
                    temp_pseudotree = extra_pseudotree[str(countExtra)]
                    for node_again in temp_pseudotree:
                        for child in temp_pseudotree[node_again]:
                            if child != node:
                                parents[child] = node_again
                                pseudotree[node_again].append(child)



            """"Get depths of every node in pseudotree"""
            depths = {}
            depths[str(self.id)] = [1]
            for node in pseudotree:

                countDepth = 0
                temp_node = node
                temp_parent = parents[temp_node]

                while temp_parent != "None":
                    countDepth += 1
                    temp_node = temp_parent
                    temp_parent = parents[temp_node]

                depths[node] = countDepth

            """Make the dictionary with string items instead of integers as is dict_nod_w_meet_nod"""
            dict_str_nod = {}
            for node in dict_nod_w_meet_nod:

                countNeighb = 1

                for neighb in dict_nod_w_meet_nod[node]:

                    if countNeighb == 1:
                        dict_str_nod[node] = [str(neighb)]
                    else:
                        dict_str_nod[node].append(str(neighb))
                    countNeighb += 1

            """Find real parents, real children, pseudoparents, pseudochildren for every node"""
            """Real parents already exist as parents[]"""
            chil = pseudotree
            pseudoparents = {}
            pseudochildren = {}
            for node in pseudotree:

                par = parents[node]
                children = pseudotree[node]
                pseudorelations = set(dict_str_nod[node]) - set([par]) - set(children)
                ps_p = []
                ps_c = []

                for relation in pseudorelations:

                    if depths[node] < depths[relation]:
                        ps_c.append(relation)
                    else:
                        ps_p.append(relation)

                pseudoparents[node] = ps_p
                pseudochildren[node] = ps_c
                pseudorelations_message = {"ps_p": ps_p, "ps_c": ps_c, "real_par": parents[node], "real_chil": chil[node]}
                if node != str(self.id):
                    udp.send_udp_mes("pseudo_relations", pseudorelations_message, self.agents_ips[node], int(self.agents_ports[node]))


                else:

                    self.pseudo_parents = ps_p
                    self.pseudo_children = ps_c
                    self.real_parents = parents[node]
                    self.real_children = chil[node]

            print("Pseudotree has been created and root has send to all agents their relations and pseudorelations.")

            """Draw constraints graph"""
            """Each vertex represents an agent and each edge is represent that two agents participates in one or more meetings
             and therefore some constraints exist for their variables"""
            constr_graph = pgv.AGraph(remincross=True)
            for node in dict_str_nod:
                for neighb in dict_str_nod[node]:
                    if not constr_graph.has_edge(node, neighb):
                        constr_graph.add_edge(node, neighb)
            constr_graph.layout(prog='dot')
            constr_graph.draw("constraints_graph.png")


            """Draw pseudotree"""
            countCycles = 0
            pseudo_draw = pgv.AGraph(remincross=True)
            for node in pseudotree:
                for child in pseudotree[node]:
                    pseudo_draw.add_edge(node, child)

            for node in dict_str_nod:
                for neighb in dict_str_nod[node]:
                    if not pseudo_draw.has_edge(node, neighb):
                        countCycles += 1
                        pseudo_draw.add_edge(node, neighb, constraint='false', style='dashed')
            print("Number of cycles: " + str(countCycles))
            pseudo_draw.layout(prog='dot')

            pseudo_draw.draw("pseudotree.png")


            """Send domain to his real and pseudo children"""
            mes_dom_util = {"dom": self.domain, "util_meet": self.utility_meet, "util_time": self.utility_time}
            for r_c in self.real_children:

                udp.send_udp_mes("domain_of_" + str(self.id), mes_dom_util, self.agents_ips[r_c], self.agents_ports[r_c])

            for p_c in self.pseudo_children:

                udp.send_udp_mes("domain_of_" + str(self.id), mes_dom_util, self.agents_ips[p_c], self.agents_ports[p_c])

        else:

            """Pseudotree creation"""

            """All agents except root send their neighbors to root to start the creation of pseudotree"""

            msg_neighb = {"neighbors": self.neighbors, "relations": self.relations}
            udp.send_udp_mes("neighbors_of_" + str(self.id), msg_neighb, self.root_IP, self.root_Port)

            """They are waiting to receive a message with information about their pseudoparents and pseudochildren from root"""
            time.sleep(2)
            while "pseudo_relations" not in msgs:
                time.sleep(2)

            pseudorel = msgs["pseudo_relations"]
            self.pseudo_parents = pseudorel['ps_p']
            self.pseudo_children = pseudorel['ps_c']
            self.real_parents = pseudorel['real_par']
            self.real_children = pseudorel['real_chil']



            """Send their domains and utilities to their real and pseudo children"""
            mes_dom_util = {"dom": self.domain, "util_meet": self.utility_meet, "util_time": self.utility_time}
            for r_c in self.real_children:

                udp.send_udp_mes("domain_of_" + str(self.id), mes_dom_util, self.agents_ips[r_c], self.agents_ports[r_c])

            for pseudo_ch in self.pseudo_children:
                udp.send_udp_mes("domain_of_" + str(self.id), mes_dom_util, self.agents_ips[pseudo_ch], self.agents_ports[pseudo_ch])

            """Wait the domains of their real and pseudo parents"""
            time.sleep(2)
            while True:

                if ("domain_of_"+self.real_parents) not in msgs:

                    time.sleep(2)

                else:
                    break

            temp_mes = msgs["domain_of_"+self.real_parents]
            self.p_pp_domains[self.real_parents] = temp_mes["dom"]
            self.p_pp_util_meet[self.real_parents] = temp_mes["util_meet"]
            self.p_pp_util_time[self.real_parents] = temp_mes["util_time"]

            while True:
                all_pseudo_parents_has_sent = True
                for pseudo_par in self.pseudo_parents:
                    if ("domain_of_" + pseudo_par) not in msgs:
                        all_pseudo_parents_has_sent = False
                        time.sleep(2)
                        break
                if all_pseudo_parents_has_sent:
                    break


            for pseudo_par in self.pseudo_parents:
                temp_mes = msgs["domain_of_" + pseudo_par]
                self.p_pp_domains[pseudo_par] = temp_mes["dom"]
                self.p_pp_util_meet[pseudo_par] = temp_mes["util_meet"]
                self.p_pp_util_time[pseudo_par] = temp_mes["util_time"]





        """Util message propagation"""

        """if a node is leaf then do:"""

        """prepare util_message"""
        if len(self.real_children) == 0:

            """Combine utilities of variables of agent like send pseudomessages among its variables"""

            relations_list = sorted(self.relations)
            index = 0
            combin_util = {}
            for meet in self.relations:

                combin = {}
                sec_index = index
                orderOfVar = {}
                count_var = 0
                orderOfVar[count_var] = relations_list[sec_index]
                if len(combin) == 0:
                    for timee in self.domain:
                        combin[str(timee)] = self.utility_meet[str(meet)] * self.utility_time[str(timee)]


                while sec_index+1 < len(relations_list):
                    orderOfVar[count_var+1] = relations_list[sec_index+1]
                    next_meet_var = relations_list[sec_index + 1]

                    temp_pos_combinations = {}
                    for combinations in combin:
                        for tim in self.domain:
                            comp = combinations.split(",")
                            equalityFlag = False
                            for index in range(len(comp)):
                                if str(tim) == comp[index]:
                                    equalityFlag = True
                                    break

                            if not equalityFlag:

                                temp_pos_combinations[combinations + "," + str(tim)] = (self.utility_meet[str(next_meet_var)]*self.utility_time[str(tim)]) + combin[combinations]

                    combin = temp_pos_combinations.copy()
                    sec_index += 1
                    count_var += 1
                combin_util = combin.copy()

            orderOfVar_array = []
            for var in orderOfVar:
                orderOfVar_array.append(orderOfVar[var])
            orderOfVar_array.reverse()

            optim_util = {}


            count_var = 0
            leng = len(orderOfVar_array)
            for var in orderOfVar_array:
                optim_util[var] = {}
                optim_util_var = optim_util[var]
                for tim in self.domain:
                    max_util = 0
                    combinats = ""
                    optim_util_remain_list = {}
                    for combinations in combin_util:


                        com = combinations.split(",")
                        if com[(leng-1)-count_var] == str(tim):
                            if combin_util[combinations] >= max_util:
                                max_util = combin_util[combinations]
                                combinats = combinations
                    optim_util_var[tim] = max_util
                    optim_util_remain_list[combinats] = max_util
                count_var += 1


            """Calculate best utilities for parent"""
            best_util_parent_meet = {}
            for meet in self.relations:
                str_meet = str(meet)
                optim_util_meet = optim_util[meet]
                if str_meet in self.p_pp_util_meet[self.real_parents]:

                    best_util_parent_meet[str_meet] = {}
                    for timee in self.p_pp_domains[self.real_parents]:
                        str_timee = str(timee)
                        max_util = 0.0
                        for timeee in self.domain:
                            str_timeee = str(timeee)
                            if timee == timeee:

                                temp_parent_util_meets = self.p_pp_util_meet[self.real_parents]
                                temp_parent_util_times = self.p_pp_util_time[self.real_parents]

                                calc_max_util = (temp_parent_util_meets[str_meet]*temp_parent_util_times[str_timee])+(optim_util_meet[timeee])
                                if calc_max_util > max_util:
                                    max_util = calc_max_util
                        best_util_parent_meet[str_meet].update({str_timee: max_util})

            mes_util_prop = {"real_parent": best_util_parent_meet}


            """Calculate best utilities for pseudoparents"""
            best_util_pseudoparent_meet = {}
            for pseudo_par in self.pseudo_parents:

                temp_best_util_ps = {}
                for meet in self.relations:
                    str_meet = str(meet)
                    if str_meet in self.p_pp_util_meet[pseudo_par]:
                        temp_best_util_ps[str_meet] = {}
                        for timee in self.p_pp_domains[pseudo_par]:
                            str_timee = str(timee)
                            max_util = 0.0
                            for timeee in self.domain:
                                str_timeee = str(timeee)
                                if timee == timeee:
                                    temp_pseudoparent_util_meets = self.p_pp_util_meet[pseudo_par]
                                    temp_pseudoparent_util_times = self.p_pp_util_time[pseudo_par]
                                    calc_max_util = (temp_pseudoparent_util_meets[str_meet] * temp_pseudoparent_util_times[str_timee]) + (self.utility_meet[str_meet] * self.utility_time[str_timeee])
                                    if calc_max_util > max_util:
                                        max_util = calc_max_util
                            temp_best_util_ps[str_meet].update({str_timee: max_util})
                best_util_pseudoparent_meet[pseudo_par] = temp_best_util_ps


            """Combine best utilities of pseudoparents with real parent values"""
            comb_best_util_pseudoparent_meet = {}
            for pseudo_par in best_util_pseudoparent_meet:
                best_util_pseudoparent_meet_pp = best_util_pseudoparent_meet[pseudo_par]
                comb_best_util_pseudoparent_meet[pseudo_par] = {}
                comb_best_util_pseudoparent_meet_pp = comb_best_util_pseudoparent_meet[pseudo_par]
                for met in best_util_pseudoparent_meet_pp:
                    best_util_pseudoparent_meet_pp_met = best_util_pseudoparent_meet_pp[met]
                    comb_best_util_pseudoparent_meet_pp[met] = {}
                    comb_best_util_pseudoparent_meet_pp_met = comb_best_util_pseudoparent_meet_pp[met]

                    orderOfVar = {}
                    count_var = 0
                    orderOfVar[count_var] = met
                    combin = best_util_pseudoparent_meet_pp_met.copy()
                    count_var += 1
                    for meet in best_util_parent_meet:
                        best_util_parent_meet_meet = best_util_parent_meet[meet]
                        orderOfVar[count_var] = meet
                        temp_pos_combinations = {}
                        for combinations in combin:
                            for tim in best_util_parent_meet_meet:

                                temp_pos_combinations[combinations + "," + str(tim)] = (best_util_parent_meet_meet[str(tim)]) + combin[combinations]

                        combin = temp_pos_combinations.copy()
                        count_var += 1
                    comb_best_util_pseudoparent_meet_pp_met["util"] = combin
                    comb_best_util_pseudoparent_meet_pp_met["order"] = orderOfVar


            mes_util_prop["pseudo_parent"] = comb_best_util_pseudoparent_meet
            countOfMessage = 0
            mes_util_prop["count_of_message"] = countOfMessage

            """send util_message to parent"""
            udp.send_udp_mes("util_mes_of_" + str(self.id), mes_util_prop, self.agents_ips[self.real_parents], self.agents_ports[self.real_parents])

            for meet in mes_util_prop["real_parent"]:
                meet_mes_util_prop = mes_util_prop["real_parent"]
                self.size_of_message += len(meet_mes_util_prop[meet])
            for pseud_par in mes_util_prop["pseudo_parent"]:
                pp_mes_util_prop = mes_util_prop["pseudo_parent"]
                meet_pp_mes_util_prop = pp_mes_util_prop[pseud_par]
                for meet in meet_pp_mes_util_prop:
                    meet_pp_mes_util_prop_meet = meet_pp_mes_util_prop[meet]
                    meet_pp_mes_util_prop_meet_util = meet_pp_mes_util_prop_meet["util"]

                    self.size_of_message += len(meet_pp_mes_util_prop_meet_util)



        else:

            """else if a node is not a leaf activate Util Message handler()"""
            if self.Port != self.root_Port:
                """if not root, wait until receive util message from your children"""

                time.sleep(2)
                while True:
                    all_children_has_sent = True
                    for chil in self.real_children:
                        if ("util_mes_of_" + chil) not in msgs:
                            all_children_has_sent = False
                            time.sleep(2)
                            break
                    if all_children_has_sent:
                        break

                countOfMessage = 0
                util_mes_child = {}
                for chil in self.real_children:
                    util_mes_child[chil] = msgs["util_mes_of_" + chil]
                    count_msg = msgs["util_mes_of_" + chil]
                    countOfMessage += count_msg["count_of_message"]
                    countOfMessage += 1


                """If all messages from children has arrived, combine utilities from them and save to your table"""
                for child in util_mes_child:
                    ut_m_ch = util_mes_child[child]
                    for meet in ut_m_ch["real_parent"]:
                        meet_ut_m_ch = ut_m_ch["real_parent"]
                        if meet not in self.combined_utilities:
                            self.combined_utilities[meet] = meet_ut_m_ch[meet]
                        else:
                            time_meet_ut_m_ch = meet_ut_m_ch[meet]
                            self_meet_comb_util = self.combined_utilities[meet]
                            for tim in self_meet_comb_util:

                                if tim not in time_meet_ut_m_ch:
                                    self_meet_comb_util.pop(tim)
                                else:
                                    temp_value = self_meet_comb_util[tim] + time_meet_ut_m_ch[tim]
                                    self_meet_comb_util[tim] = temp_value

                    pp_util_m_ch = ut_m_ch["pseudo_parent"]

                    if str(self.id) in pp_util_m_ch:
                        for meet in pp_util_m_ch[str(self.id)]:
                            meet_pp_util_m_ch = pp_util_m_ch[str(self.id)]
                            if meet not in self.combined_utilities:
                                self.combined_utilities[meet] = meet_pp_util_m_ch[meet]
                            else:
                                time_meet_pp_util_m_ch = meet_pp_util_m_ch[meet]
                                self_meet_comb_util = self.combined_utilities[meet]
                                for tim in self_meet_comb_util:
                                    if tim not in time_meet_pp_util_m_ch:
                                        self_meet_comb_util.pop(tim)
                                    else:
                                        temp_value = self_meet_comb_util[tim] + time_meet_pp_util_m_ch[tim]
                                        self_meet_comb_util[tim] = temp_value



                """Combine utilities for parents and pseudoparents"""
                temp_util_combination = {}
                for meet in self.relations:

                    str_meet = str(meet)
                    if str_meet in self.p_pp_util_meet[self.real_parents]:
                        temp_util_combination[str_meet] = {}
                        for timee in self.domain:
                            str_timee = str(timee)
                            temp_ut = 0.0

                            for child_mes in util_mes_child:
                                umc = util_mes_child[child_mes]
                                for meeting in umc["real_parent"]:
                                    m = umc["real_parent"]
                                    mm = m[meeting]
                                    for timeee in mm:
                                        str_timeee = str(timeee)
                                        if str_timeee == str_timee:
                                            temp_ut += mm[timeee]

                            for pseudoch_mes in util_mes_child:
                                ump = util_mes_child[pseudoch_mes]

                                umpm = ump["pseudo_parent"]
                                if str(self.id) in umpm:
                                    sh_umpm = umpm[str(self.id)]
                                    for m in sh_umpm:
                                        meet_sh_umpm = sh_umpm[m]
                                        if "order" not in meet_sh_umpm:
                                            for timeee in meet_sh_umpm:
                                                str_timeee = str(timeee)
                                                if str_timeee == str_timee:
                                                    temp_ut += meet_sh_umpm[timeee]

                            temp_util_combination[str_meet].update({str_timee: temp_ut})


                """Reduce your dimension from pseudochildren dimensions part of message"""
                remain_pseudochilden = {}
                for chil in self.real_children:
                    util_mes = util_mes_child[chil]
                    pseud_util_mes = util_mes["pseudo_parent"]
                    for pseudo_p in pseud_util_mes:
                        if pseudo_p != str(self.id):
                            pseud_util_mes_pseudo_p = pseud_util_mes[pseudo_p]
                            temp_util_pp = {}
                            for meet in pseud_util_mes_pseudo_p:
                                pseud_util_mes_pseudo_p_meet = pseud_util_mes_pseudo_p[meet]
                                if "util" not in pseud_util_mes_pseudo_p_meet:
                                    temp_util_pp[meet] = pseud_util_mes_pseudo_p_meet
                                    continue
                                pseud_util_mes_pseudo_p_meet_util = pseud_util_mes_pseudo_p_meet["util"]
                                pseud_util_mes_pseudo_p_meet_order = pseud_util_mes_pseudo_p_meet["order"]
                                dom = []
                                for combination in pseud_util_mes_pseudo_p_meet_util:

                                    for i in range(len(pseud_util_mes_pseudo_p_meet_order)-1):

                                        met = pseud_util_mes_pseudo_p_meet_order[str(i+1)]

                                        com = combination.split(",")
                                        if met in temp_util_combination:

                                            temp_util_combination_met = temp_util_combination[met]
                                            if com[i+1] in temp_util_combination_met:
                                                pseud_util_mes_pseudo_p_meet_util[combination] += temp_util_combination_met[com[i+1]]
                                                if com[i+1] not in dom:
                                                    dom.append(com[i+1])
                                temp_util_pseud = {}
                                for t in range(len(dom)):
                                    maxim = 0.0
                                    for combination in pseud_util_mes_pseudo_p_meet_util:
                                        com = combination.split(",")
                                        if com[0] == dom[t]:
                                            if pseud_util_mes_pseudo_p_meet_util[combination] > maxim:
                                                maxim = pseud_util_mes_pseudo_p_meet_util[combination]
                                    temp_util_pseud[dom[t]] = maxim
                                temp_util_pp[meet] = temp_util_pseud.copy()
                            pseud_util_mes[pseudo_p] = temp_util_pp.copy()


                            if pseudo_p not in remain_pseudochilden:
                                remain_pseudochilden[pseudo_p] = pseud_util_mes[pseudo_p]
                            else:
                                for meett in pseud_util_mes[pseudo_p]:
                                    meet_pseud_util_mes = pseud_util_mes[pseudo_p]
                                    if meett not in remain_pseudochilden[pseudo_p]:

                                        remain_pseudochilden[pseudo_p].update({meett: meet_pseud_util_mes[meett]})
                                    else:
                                        temp_remain_pseudochildren = remain_pseudochilden[pseudo_p]
                                        for timm in meet_pseud_util_mes[meett]:
                                            time_meet_pseud_util_mes = meet_pseud_util_mes[meett]
                                            if timm in temp_remain_pseudochildren[meett]:

                                                temp_meet_remain_pseudochildren = temp_remain_pseudochildren[meett]
                                                temp_meet_remain_pseudochildren[timm] += time_meet_pseud_util_mes[timm]
                                        for timm in temp_remain_pseudochildren[meett]:
                                            time_meet_pseud_util_mes = meet_pseud_util_mes[meett]
                                            if timm not in time_meet_pseud_util_mes:
                                                temp_remain_pseudochildren[meett].pop(timm)


                """Combine utilities of variables of agent like send pseudomessages among its variables"""

                relations_list = sorted(self.relations)
                index = 0
                combin_util = {}
                for meet in self.relations:

                    combin = {}
                    sec_index = index
                    orderOfVar = {}
                    count_var = 0
                    orderOfVar[count_var] = relations_list[sec_index]
                    if len(combin) == 0:

                        for timee in self.domain:
                            combin[str(timee)] = (self.utility_meet[str(meet)] * self.utility_time[str(timee)])
                            if str(meet) in temp_util_combination:
                                temp_util_combination_meet = temp_util_combination[str(meet)]
                                if str(timee) in temp_util_combination_meet:
                                    combin[str(timee)] += temp_util_combination_meet[str(timee)]

                    while sec_index + 1 < len(relations_list):
                        orderOfVar[count_var + 1] = relations_list[sec_index + 1]
                        next_meet_var = relations_list[sec_index + 1]

                        temp_pos_combinations = {}
                        for combinations in combin:
                            for tim in self.domain:
                                comp = combinations.split(",")
                                equalityFlag = False
                                for index in range(len(comp)):
                                    if str(tim) == comp[index]:
                                        equalityFlag = True
                                        break

                                if not equalityFlag:

                                    if str(next_meet_var) in temp_util_combination:
                                        temp_util_combination_meet = temp_util_combination[str(next_meet_var)]
                                        if str(tim) in temp_util_combination_meet:
                                            temp_pos_combinations[combinations + "," + str(tim)] = (self.utility_meet[str(next_meet_var)] * self.utility_time[str(tim)]) + temp_util_combination_meet[str(tim)] + combin[combinations]
                                        else:
                                            temp_pos_combinations[combinations + "," + str(tim)] = (self.utility_meet[str(next_meet_var)] * self.utility_time[str(tim)]) + combin[combinations]
                                    else:
                                        temp_pos_combinations[combinations + "," + str(tim)] = (self.utility_meet[str(next_meet_var)] * self.utility_time[str(tim)]) + combin[combinations]
                        combin = temp_pos_combinations.copy()
                        sec_index += 1
                        count_var += 1
                    combin_util = combin.copy()

                orderOfVar_array = []
                for var in orderOfVar:
                    orderOfVar_array.append(orderOfVar[var])
                orderOfVar_array.reverse()

                optim_util = {}

                count_var = 0
                leng = len(orderOfVar_array)
                for var in orderOfVar_array:
                    optim_util[var] = {}
                    optim_util_var = optim_util[var]
                    for tim in self.domain:

                        max_util = 0
                        combinats = ""
                        optim_util_remain_list = {}
                        for combinations in combin_util:

                            com = combinations.split(",")
                            if com[(leng - 1) - count_var] == str(tim):
                                if combin_util[combinations] >= max_util:
                                    max_util = combin_util[combinations]
                                    combinats = combinations
                        optim_util_var[tim] = max_util
                        optim_util_remain_list[combinats] = max_util
                    count_var += 1


                """Now prepare util message to send to your parent"""
                """Calculate best utilities for parent"""
                best_util_parent_meet = {}
                for meet in temp_util_combination:
                    optim_util_meet = optim_util[int(meet)]
                    best_util_parent_meet[meet] = {}
                    for timee in self.p_pp_domains[self.real_parents]:
                        str_timee = str(timee)
                        max_util = 0.0
                        for timeee in self.domain:
                            str_timeee = str(timeee)
                            if timee == timeee:
                                temp_parent_util_meets = self.p_pp_util_meet[self.real_parents]
                                temp_parent_util_times = self.p_pp_util_time[self.real_parents]

                                calc_max_util = (temp_parent_util_meets[meet] * temp_parent_util_times[str_timee]) + (optim_util_meet[timeee])
                                if calc_max_util > max_util:
                                    max_util = calc_max_util
                        best_util_parent_meet[meet].update({str_timee: max_util})


                """Calculate best utilities for pseudoparents"""
                best_util_pseudoparent_meet = {}
                for pseudo_par in self.pseudo_parents:

                    temp_best_util_ps = {}
                    for meet in self.relations:
                        str_meet = str(meet)
                        if str_meet in self.p_pp_util_meet[pseudo_par]:
                            temp_best_util_ps[str_meet] = {}
                            for timee in self.p_pp_domains[pseudo_par]:
                                str_timee = str(timee)
                                max_util = 0.0
                                for timeee in self.domain:
                                    str_timeee = str(timeee)
                                    if timee == timeee:
                                        temp_pseudoparent_util_meets = self.p_pp_util_meet[pseudo_par]
                                        temp_pseudoparent_util_times = self.p_pp_util_time[pseudo_par]
                                        calc_max_util = (temp_pseudoparent_util_meets[str_meet] * temp_pseudoparent_util_times[str_timee]) + (self.utility_meet[str_meet] * self.utility_time[str_timeee])
                                        if calc_max_util > max_util:
                                            max_util = calc_max_util
                                temp_best_util_ps[str_meet].update({str_timee: max_util})
                    best_util_pseudoparent_meet[pseudo_par] = temp_best_util_ps



                """Combine best utilities of pseudoparents with real parent values"""
                comb_best_util_pseudoparent_meet = {}
                for pseudo_par in best_util_pseudoparent_meet:
                    best_util_pseudoparent_meet_pp = best_util_pseudoparent_meet[pseudo_par]
                    comb_best_util_pseudoparent_meet[pseudo_par] = {}
                    comb_best_util_pseudoparent_meet_pp = comb_best_util_pseudoparent_meet[pseudo_par]
                    for met in best_util_pseudoparent_meet_pp:
                        best_util_pseudoparent_meet_pp_met = best_util_pseudoparent_meet_pp[met]
                        comb_best_util_pseudoparent_meet_pp[met] = {}
                        comb_best_util_pseudoparent_meet_pp_met = comb_best_util_pseudoparent_meet_pp[met]

                        orderOfVar = {}
                        count_var = 0
                        orderOfVar[count_var] = met
                        combin = best_util_pseudoparent_meet_pp_met.copy()
                        count_var += 1
                        for meet in best_util_parent_meet:
                            best_util_parent_meet_meet = best_util_parent_meet[meet]
                            orderOfVar[count_var] = meet
                            temp_pos_combinations = {}
                            for combinations in combin:
                                for tim in best_util_parent_meet_meet:
                                    temp_pos_combinations[combinations + "," + str(tim)] = (best_util_parent_meet_meet[str(tim)]) + combin[combinations]
                            combin = temp_pos_combinations.copy()
                            count_var += 1
                        comb_best_util_pseudoparent_meet_pp_met["util"] = combin
                        comb_best_util_pseudoparent_meet_pp_met["order"] = orderOfVar


                """Add pseudoparent part in message and combine them with the remaining pseudoparent part of message of your children"""
                for pseudo_par in remain_pseudochilden:
                    if pseudo_par not in comb_best_util_pseudoparent_meet:
                        comb_best_util_pseudoparent_meet[pseudo_par] = remain_pseudochilden[pseudo_par]
                    else:
                        for meet in remain_pseudochilden[pseudo_par]:
                            meet_remain_pseudochildren = remain_pseudochilden[pseudo_par]
                            if meet not in comb_best_util_pseudoparent_meet[pseudo_par]:
                                comb_best_util_pseudoparent_meet[pseudo_par].update({meet: meet_remain_pseudochildren[meet]})
                            else:
                                meet_best_util_pseudopar = comb_best_util_pseudoparent_meet[pseudo_par]
                                time_meet_remain_pseudochildren = meet_remain_pseudochildren[meet]
                                if "util" not in meet_best_util_pseudopar[meet]:

                                    for tim in time_meet_remain_pseudochildren:

                                        if tim in meet_best_util_pseudopar[meet]:

                                            time_meet_best_util_pseudopar = meet_best_util_pseudopar[meet]
                                            time_meet_best_util_pseudopar[tim] += time_meet_remain_pseudochildren[tim]
                                    for tim in meet_best_util_pseudopar[meet]:
                                        if tim not in time_meet_remain_pseudochildren:
                                            meet_best_util_pseudopar[meet].pop(tim)
                                else:
                                    time_meet_best_util_pseudopar = meet_best_util_pseudopar[meet]
                                    time_meet_best_util_pseudopar_util = time_meet_best_util_pseudopar["util"]
                                    for combination in time_meet_best_util_pseudopar_util:
                                        com = combination.split(",")
                                        for t in time_meet_remain_pseudochildren:
                                            if t == com[0]:
                                                time_meet_best_util_pseudopar_util[combination] += time_meet_remain_pseudochildren[t]
                                                break

                mes_util_prop = {"real_parent": best_util_parent_meet, "pseudo_parent": comb_best_util_pseudoparent_meet, "count_of_message": countOfMessage}


                """send util_message to parent"""
                udp.send_udp_mes("util_mes_of_" + str(self.id), mes_util_prop, self.agents_ips[self.real_parents], self.agents_ports[self.real_parents])

                for meet in mes_util_prop["real_parent"]:
                    meet_mes_util_prop = mes_util_prop["real_parent"]
                    self.size_of_message += len(meet_mes_util_prop[meet])
                for pseud_par in mes_util_prop["pseudo_parent"]:
                    pp_mes_util_prop = mes_util_prop["pseudo_parent"]
                    for meet in pp_mes_util_prop[pseud_par]:
                        meet_pp_mes_util_prop = pp_mes_util_prop[pseud_par]
                        if "util" in meet_pp_mes_util_prop[meet]:
                            meet_pp_mes_util_prop_meet = meet_pp_mes_util_prop[meet]
                            self.size_of_message += len(meet_pp_mes_util_prop_meet["util"])
                        else:
                            self.size_of_message += len(meet_pp_mes_util_prop[meet])


                """Send the maximum message size at root to be printed"""
                my_val = {"message_size": self.size_of_message}
                udp.send_udp_mes("my_values_" + str(self.id), my_val, self.root_IP, self.root_Port)



            else:
                """Else if node is root do:"""
                """Activate Util Message handler()"""
                """Wait until receive util message from your children"""
                print("UTIL message propagation phase has begun. Root is waiting messages from his children.")
                time.sleep(2)
                while True:
                    all_children_has_sent = True
                    for chil in self.real_children:
                        if ("util_mes_of_" + chil) not in msgs:
                            all_children_has_sent = False
                            time.sleep(2)
                            break
                    if all_children_has_sent:
                        break

                util_mes_child = {}
                countOfMessage = 0
                for chil in self.real_children:
                    util_mes_child[chil] = msgs["util_mes_of_" + chil]
                    count_msg = msgs["util_mes_of_" + chil]
                    countOfMessage += count_msg["count_of_message"]
                    countOfMessage += 1

                print("UTIL messages has received from root. He will choose optimal values and the VALUE message propagation phase will begin. ")
                """Calculate optimal values for his variables depends on children's messages"""
                optim_values = {}
                for chil in util_mes_child:
                    chil_util_mes_child = util_mes_child[chil]
                    for meet in chil_util_mes_child["real_parent"]:
                        meet_chil_util_mes_child = chil_util_mes_child["real_parent"]
                        if meet not in optim_values:

                            optim_values[meet] = meet_chil_util_mes_child[meet]
                        else:
                            for tim in optim_values[meet]:
                                if tim not in meet_chil_util_mes_child[meet]:
                                    optim_values[meet].pop(tim)
                                else:
                                    time_meet_chil_util_mes_child = meet_chil_util_mes_child[meet]
                                    meet_optim_values = optim_values[meet]
                                    temp_value = time_meet_chil_util_mes_child[tim] + meet_optim_values[tim]
                                    meet_optim_values[tim] = temp_value
                    for pseudo_c in chil_util_mes_child["pseudo_parent"]:
                        ps_c_chil_util_mes_child = chil_util_mes_child["pseudo_parent"]
                        for meet in ps_c_chil_util_mes_child[pseudo_c]:
                            meet_ps_c_chil_util_mes_child = ps_c_chil_util_mes_child[pseudo_c]
                            if meet not in optim_values:
                                optim_values[meet] = meet_ps_c_chil_util_mes_child[meet]
                            else:
                                for tim in optim_values[meet]:
                                    if tim not in meet_ps_c_chil_util_mes_child[meet]:
                                        optim_values[meet].pop(tim)
                                    else:
                                        time_meet_ps_c_chil_util_mes_child = meet_ps_c_chil_util_mes_child[meet]
                                        meet_optim_values = optim_values[meet]
                                        temp_value = meet_optim_values[tim] + time_meet_ps_c_chil_util_mes_child[tim]
                                        meet_optim_values[tim] = temp_value
                pos_combinations = {}
                countVar = 0
                orderOfVar = {}
                for variable in optim_values:
                    if countVar == 0:
                        orderOfVar[countVar] = variable
                        pos_combinations = optim_values[variable]
                        countVar += 1
                    else:
                        orderOfVar[countVar] = variable
                        temp_pos_combinations = {}
                        for combinations in pos_combinations:

                            for dom in optim_values[variable]:
                                comp = combinations.split(",")
                                equalityFlag = False
                                for index in range(len(comp)):
                                    if dom == comp[index]:
                                        equalityFlag = True
                                        break
                                if not equalityFlag:

                                    var_optim_values = optim_values[variable]
                                    temp_pos_combinations[combinations + "," + dom] = var_optim_values[dom] + pos_combinations[combinations]
                        countVar += 1
                        pos_combinations = temp_pos_combinations

                best_vars_val = 0
                index_vars_val = 0
                for combination in pos_combinations:
                    if best_vars_val < pos_combinations[combination]:
                        best_vars_val = pos_combinations[combination]
                        index_vars_val = combination
                final_optimal_value_per_var = {}
                for i in range(len(orderOfVar)):
                    parse_index_vars_val = index_vars_val.split(",")
                    final_optimal_value_per_var[orderOfVar[i]] = parse_index_vars_val[i]


                """Prepare and send VALUE message to your children"""
                value_mes_prop = {}
                real_children_value_mes = {}
                pseudo_children_value_mes = {}
                for child in self.real_children:
                    for meet in self.relations:

                        for node in self.relations[meet]:
                            if str(child) == str(node):
                                if str(child) not in real_children_value_mes:
                                    real_children_value_mes[str(child)] = {str(meet): final_optimal_value_per_var[str(meet)]}
                                else:
                                    real_children_value_mes[str(child)].update({str(meet): final_optimal_value_per_var[str(meet)]})
                    value_mes_prop = {"real_child": real_children_value_mes[str(child)]}
                    pseud_ch_in_mes_from_child = msgs["util_mes_of_" + child]
                    meets_pseud_ch_in_mes_from_child = pseud_ch_in_mes_from_child["pseudo_parent"]
                    for meet in meets_pseud_ch_in_mes_from_child[str(self.id)]:
                        if str(child) not in pseudo_children_value_mes:
                            pseudo_children_value_mes[str(child)] = {meet: final_optimal_value_per_var[meet]}
                        else:
                            pseudo_children_value_mes[str(child)].update({meet: final_optimal_value_per_var[meet]})
                    value_mes_prop["pseudo_children"] = pseudo_children_value_mes[str(child)]
                    udp.send_udp_mes("value_message", value_mes_prop, self.agents_ips[str(child)], self.agents_ports[str(child)])

                    """Algorithm has ended for root. Wait for the messages of all agents with their chosen values and size of util message"""

                    time.sleep(2)
                    while True:
                        all_agents_has_sent = True
                        for agent in self.only_root_know_list_agents:

                            if ("my_values_" + agent) not in msgs:
                                all_agents_has_sent = False
                                time.sleep(2)
                                break
                        if all_agents_has_sent:
                            break
                    print("VALUE message propagation phase has ended. Now root will print the results.")
                    selected_values = {}
                    max_size_of_message = 0
                    for agent in self.only_root_know_list_agents:
                        values_in_msg = msgs["my_values_" + agent]
                        for meet in values_in_msg["values"]:
                            if meet not in selected_values:
                                meet_message = values_in_msg["values"]
                                selected_values[meet] = meet_message[meet]
                        if max_size_of_message < values_in_msg["message_size"]:
                            max_size_of_message = values_in_msg["message_size"]
                    for meet in final_optimal_value_per_var:
                        if meet not in selected_values:
                            selected_values[meet] = final_optimal_value_per_var[meet]
                    for i in range(len(selected_values)):
                        print("Meeting with ID: " + str(i+1) + " will take place in time interval: " + selected_values[str(i)])
                    print("Maximum size of message is: " + str(max_size_of_message))
                    print("Number of messages: " + str((countOfMessage * 2)))



        """if not root activate VALUE_message_handler() """
        """Wait for the VALUE message of your parent"""
        if self.Port != self.root_Port:
            time.sleep(2)
            while True:

                if "value_message" not in msgs:

                    time.sleep(2)

                else:
                    break

            """When the message has come, see the values that your parent has chosen for your common meetings"""
            chosen_values_of_meetings = {}
            value_mes = msgs["value_message"]
            for meet in value_mes["real_child"]:
                meet_value_mes = value_mes["real_child"]
                chosen_values_of_meetings[meet] = meet_value_mes[meet]
            for meet in value_mes["pseudo_children"]:
                for met in self.relations:
                    if meet == str(met):
                        if meet not in chosen_values_of_meetings:
                            meet_value_mes = value_mes["pseudo_children"]
                            chosen_values_of_meetings[meet] = meet_value_mes[meet]


            """If not a leaf then do:"""
            """Combine the values for the meetings which has been chosen from your parent, with the values for the variables of meetings which are common with your children and pseudochildren and choose the optimal values"""
            if len(self.real_children) != 0:
                for meet in chosen_values_of_meetings:
                    if meet in self.combined_utilities:
                        self.combined_utilities.pop(meet)

                pos_combinations = {}
                countVar = 0
                orderOfVar = {}
                for variable in self.combined_utilities:
                    if countVar == 0:
                        orderOfVar[countVar] = variable
                        equalityFlag = False
                        for dom in self.combined_utilities[variable]:
                            equalityFlag = False
                            for meet in chosen_values_of_meetings:
                                if chosen_values_of_meetings[meet] == dom:
                                    equalityFlag = True
                                    break
                            if not equalityFlag:
                                var_self_comb_util = self.combined_utilities[variable]
                                pos_combinations[dom] = var_self_comb_util[dom]

                        countVar += 1
                    else:
                        orderOfVar[countVar] = variable
                        temp_pos_combinations = {}
                        for combinations in pos_combinations:

                            for dom in self.combined_utilities[variable]:
                                comp = combinations.split(",")
                                equalityFlag = False
                                for index in range(len(comp)):
                                    if dom == comp[index]:
                                        equalityFlag = True
                                        break
                                if not equalityFlag:
                                    for meet in chosen_values_of_meetings:
                                        if chosen_values_of_meetings[meet] == comp[index] or chosen_values_of_meetings[meet] == dom:
                                            equalityFlag = True
                                            break
                                if not equalityFlag:
                                    var_self_comb_util = self.combined_utilities[variable]
                                    temp_pos_combinations[combinations + "," + dom] = var_self_comb_util[dom] + pos_combinations[combinations]
                        countVar += 1
                        pos_combinations = temp_pos_combinations

                best_vars_val = 0
                index_vars_val = 0
                for combination in pos_combinations:
                    if best_vars_val < pos_combinations[combination]:
                        best_vars_val = pos_combinations[combination]
                        index_vars_val = combination
                final_optimal_value_per_var = {}
                for i in range(len(orderOfVar)):
                    parse_index_vars_val = index_vars_val.split(",")
                    final_optimal_value_per_var[orderOfVar[i]] = parse_index_vars_val[i]



                """Prepare and send VALUE message to your children"""
                value_mes_prop = {}
                real_children_value_mes = {}
                pseudo_children_value_mes = {}
                for child in self.real_children:
                    for meet in self.relations:

                        for node in self.relations[meet]:
                            if str(child) == str(node):
                                if str(child) not in real_children_value_mes:
                                    if str(meet) in final_optimal_value_per_var:
                                        real_children_value_mes[str(child)] = {str(meet): final_optimal_value_per_var[str(meet)]}
                                    elif str(meet) in chosen_values_of_meetings:
                                        real_children_value_mes[str(child)] = {str(meet): chosen_values_of_meetings[str(meet)]}
                                else:
                                    if str(meet) in final_optimal_value_per_var:
                                        real_children_value_mes[str(child)].update({str(meet): final_optimal_value_per_var[str(meet)]})
                                    elif str(meet) in chosen_values_of_meetings:
                                        real_children_value_mes[str(child)].update({str(meet): chosen_values_of_meetings[str(meet)]})
                    if str(child) in real_children_value_mes:

                        value_mes_prop = {"real_child": real_children_value_mes[str(child)]}
                    else:
                        value_mes_prop["real_child"] = {}
                    pseud_ch_in_mes_from_child = msgs["util_mes_of_" + child]
                    meets_pseud_ch_in_mes_from_child = pseud_ch_in_mes_from_child["pseudo_parent"]
                    if str(self.id) in meets_pseud_ch_in_mes_from_child:
                        for meet in meets_pseud_ch_in_mes_from_child[str(self.id)]:
                            if str(child) not in pseudo_children_value_mes:
                                if meet in final_optimal_value_per_var:
                                    pseudo_children_value_mes[str(child)] = {meet: final_optimal_value_per_var[meet]}
                                elif meet in chosen_values_of_meetings:
                                    pseudo_children_value_mes[str(child)] = {meet: chosen_values_of_meetings[meet]}
                            else:
                                if meet in final_optimal_value_per_var:
                                    pseudo_children_value_mes[str(child)].update({meet: final_optimal_value_per_var[meet]})
                                elif meet in chosen_values_of_meetings:
                                    pseudo_children_value_mes[str(child)].update({meet: chosen_values_of_meetings[meet]})
                        for meet in value_mes["pseudo_children"]:
                            if meet not in pseudo_children_value_mes[str(child)]:
                                meet_value_msg = value_mes["pseudo_children"]
                                pseudo_children_value_mes[str(child)].update({meet: meet_value_msg[meet]})
                    else:
                        pseudo_children_value_mes[str(child)] = {}
                        for meet in value_mes["pseudo_children"]:
                            if meet not in pseudo_children_value_mes[str(child)]:
                                meet_value_msg = value_mes["pseudo_children"]
                                pseudo_children_value_mes[str(child)].update({meet: meet_value_msg[meet]})

                    value_mes_prop["pseudo_children"] = pseudo_children_value_mes[str(child)]
                    udp.send_udp_mes("value_message", value_mes_prop, self.agents_ips[str(child)], self.agents_ports[str(child)])


                """Send the selected values for your meetings, the maximum message size at root to be printed"""
                my_val = {"values": final_optimal_value_per_var, "message_size": self.size_of_message}
                udp.send_udp_mes("my_values_" + str(self.id), my_val, self.root_IP, self.root_Port)


            else:
                """else if you are a leaf, then the algorithm has ended, so do:"""
                """Send the selected values for your meetings, the maximum message size at root to be printed"""
                my_val = {"values": {}, "message_size": self.size_of_message}
                udp.send_udp_mes("my_values_" + str(self.id), my_val, self.root_IP, self.root_Port)
