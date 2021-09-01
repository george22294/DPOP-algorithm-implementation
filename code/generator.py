import sys
import random
import math
import pygraphviz as pgv

class node:

    def __init__(self, _id):
        self.id = _id
        self.children = {}
        self.parent = None
        self.siblings = {}
        self.meetings = {}
        # agent may prefer later meetings , earlier meeting or do not care about the time at all
        possible_time_slot_utils = [[10, 20, 30, 40, 50, 60, 70, 80], [80, 70, 60, 50, 40, 30, 20, 10],
                                    [10, 10, 10, 10, 10, 10, 10, 10]]
        self.timeslot_utils = random.choice(possible_time_slot_utils)

    def print_node_info(self):
        print("-------------------------------------")
        print("Node id: " + str(self.id))
        if (self.parent != None):
            print("Parent: " + str(self.parent.id))
        else:
            print("Parent: None")
        print("Children", list(self.children.keys()))
        print("Siblings", list(self.siblings.keys()))
        print("Meetings", self.meetings)
        print("-------------------------------------")


class meetings():

    def __init__(self, node_index):
        self.total_meetings = 0
        self.meeting_index = {}
        self.node_index = node_index
        # choice is random / see below
        self.possible_meeting_util = [100, 70, 50, 10]
        self.M = math.ceil(len(node_index) / 2)
        self.GRP_num = 0
        self.PTC_num = 0
        self.SIB_num = 0
        self.num_vars = 0

    def print_meeting_distribution(self):
        print("GRP: " + str(self.GRP_num))
        print("PTC: " + str(self.PTC_num))
        print("SIB: " + str(self.SIB_num))
        print("Total: " + str(self.total_meetings))
        print("Total Variables: ", self.num_vars)

    def calculate_variable_num(self):

        for node in self.node_index.values():
            self.num_vars += len(node.meetings)

    def create_meetings(self, _id, kind_of_meeting):

        if kind_of_meeting == "SIB":
            if self.create_SIB(_id):
                return True
            else:
                return False
        elif kind_of_meeting == "PTC":
            if self.create_PTC(_id):
                return True
            else:
                return False
        elif kind_of_meeting == "GRP":
            if self.create_GRP(_id):
                return True
            else:
                return False


    def create_GRP(self, _id):
        node = self.node_index[_id]
        if (len(node.children) == 0 or len(
                node.meetings) == 8):
            return False
        # print("GRP meeting "+str(node.id))
        ml = [node.id]

        for cn in node.children.keys():
            if len(node.children[cn].meetings) < 8:
                ml.append(node.children[cn].id)
            else:
                return False

        ml = list(sorted(ml))
        if ml in self.meeting_index.values():
            return False

        for cn in node.children.keys():
            node.children[cn].meetings[self.total_meetings] = random.choice(self.possible_meeting_util)

        node.meetings[self.total_meetings] = random.choice(self.possible_meeting_util)
        self.meeting_index[self.total_meetings] = ml
        self.total_meetings += 1
        self.GRP_num += 1
        # print(ml)
        return True

    def create_PTC(self, _id):
        node = self.node_index[_id]
        if (node.parent == None or len(
                node.meetings) == 8):
            return False

        # print("PTC meeting "+str(node.id))
        ml = [node.id]

        if len(node.parent.meetings) < 8:
            ml.append(node.parent.id)
        else:
            return False

        ml = list(sorted(ml))
        if ml in self.meeting_index.values():
            return False

        for sib in node.siblings.keys():
            ml = [node.siblings[sib].id, node.parent.id]
            ml = list(sorted(ml))
            if ml in self.meeting_index.values():
                return False

        node.parent.meetings[self.total_meetings] = random.choice(self.possible_meeting_util)
        node.meetings[self.total_meetings] = random.choice(self.possible_meeting_util)
        self.meeting_index[self.total_meetings] = ml
        self.total_meetings += 1
        self.PTC_num += 1
        # print(ml)
        return True

    def create_SIB(self, _id):
        node = self.node_index[_id]
        if (len(node.siblings) == 0 or len(
                node.meetings) == 8):
            return False
        # print("SIB meeting "+str(node.id))

        ml = [node.id]

        for cn in node.siblings.keys():
            if len(node.siblings[cn].meetings) < 8:
                ml.append(node.siblings[cn].id)
            else:
                return False

        ml = list(sorted(ml))
        if ml in self.meeting_index.values():
            return False

        for cn in node.siblings.keys():
            node.siblings[cn].meetings[self.total_meetings] = random.choice(self.possible_meeting_util)

        node.meetings[self.total_meetings] = random.choice(self.possible_meeting_util)
        self.meeting_index[self.total_meetings] = ml
        self.total_meetings += 1
        self.SIB_num += 1
        # print(ml)
        return True


def divide_list(l, n):
    for i in range(0, len(l), n):
        yield l[i:i + n]


def flatten_list(list_of_lists):
    flattened = []
    for sublist in list_of_lists:
        for val in sublist:
            flattened.append(val)
    return flattened


def create_hierarchy(N):
    level = 1
    total_nodes = 0
    i = 0

    index = {}
    multiplier = 1

    while (total_nodes < N):

        l = []
        child_num = 0
        while (child_num < multiplier):
            if (total_nodes >= N):
                break
            l.append(total_nodes)
            cn = node(total_nodes)
            index[total_nodes] = cn
            total_nodes += 1
            child_num += 1

        ll = list(divide_list(l, level))
        if (level != 1):
            flat_parent_list = flatten_list(prev_level_parents)
            for i in range(0, len(flat_parent_list)):
                p = flat_parent_list[i]
                parent_node = index[p]
                try:
                    for c in ll[i]:
                        child_node = index[c]
                        parent_node.children[child_node.id] = child_node
                        child_node.parent = parent_node
                        for s in ll[i]:
                            if s != c:
                                sibling_node = index[s]
                                child_node.siblings[sibling_node.id] = sibling_node
                except IndexError as e:
                    return index

        prev_level_parents = ll
        # print(ll)
        level += 1
        multiplier *= level

    return index


def export_to_file(node_index, N, M, V):
    f = open("DCOP_Problem_" + str(N), "w")
    f.write(str(N) + ";" + str(M) + ";" + str(V) + "\n")
    for node in node_index.values():
        for m in node.meetings.keys():
            f.write(str(node.id) + ";" + str(m) + ";" + str(node.meetings[m]) + "\n")

    for node in node_index.values():
        for i in range(0, len(node.timeslot_utils)):
            f.write(str(node.id) + ";" + str(i) + ";" + str(node.timeslot_utils[i]) + "\n")


def main():
    """N is the number of agents"""
    N = 9


    index = create_hierarchy(N)

    """Draw hierarchy tree"""
    constr_graph = pgv.AGraph(remincross=True)
    for nod in index:
        childrenn = index[nod].children
        for child in childrenn:

            if not constr_graph.has_edge(str(index[nod].id), str(childrenn[child].id)):
                constr_graph.add_edge(str(index[nod].id), str(childrenn[child].id))
    constr_graph.layout(prog='dot')
    constr_graph.draw("hierarchy_tree.png")

    MM = meetings(index)

    inverse_index = []
    for n in index.keys():
        inverse_index.append(n)
    inverse_index.reverse()

    if round(MM.M/3) < MM.M/3:
        n_SIB_M = round(MM.M/3) + 1
        n_GRB_M = round(MM.M/3)
        n_PTC_M = round(MM.M/3)
    elif round(MM.M/3) > MM.M/3:
        n_SIB_M = round(MM.M / 3)
        n_GRB_M = round(MM.M / 3)
        n_PTC_M = round(MM.M / 3) - 1
    else:
        n_SIB_M = round(MM.M / 3)
        n_GRB_M = round(MM.M / 3)
        n_PTC_M = round(MM.M / 3)

    count_SIB_M = 0
    count_GRB_M = 0
    count_PTC_M = 0
    for n in range(len(inverse_index)):
        if count_SIB_M < n_SIB_M and MM.create_meetings(inverse_index[n], "SIB"):

            count_SIB_M += 1
        elif count_PTC_M < n_PTC_M and MM.create_meetings(inverse_index[n], "PTC"):
            count_PTC_M += 1
    for n in index.keys():
        if count_GRB_M < n_GRB_M and MM.create_meetings(n, "GRP"):
            count_GRB_M += 1


    MM.calculate_variable_num()
    MM.print_meeting_distribution()
    export_to_file(index, N, MM.M, MM.num_vars)


if __name__ == '__main__':
    main()
