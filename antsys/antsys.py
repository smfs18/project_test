import random

import numpy as np


class Edge:
    def __init__(self, start, end, info, pheromone=0.1):
        self.start = start
        self.end = end
        self.info = info
        self.pheromone = pheromone


class AntWorld:
    def __init__(self, nodes, r_func, c_func, h_func, complete=True, init_phe=0.1):
        self.nodes = nodes
        self.complete = complete

        self.init_phe = init_phe

        self.r_func = r_func
        self.c_func = c_func
        self.h_func = h_func

        self._create_edges()

    def _create_edges(self):
        self.edges = []

        if self.complete:
            for start in self.nodes:
                for end in self.nodes:
                    if start is not end:
                        info_list = self.r_func(start, end)
                        for info in info_list:
                            self.edges.append(Edge(start, end, info, self.init_phe))
        else:
            for i in range(-1, len(self.nodes) - 1):
                start = self.nodes[i]
                end = self.nodes[i + 1]
                info_list = self.r_func(start, end)
                for info in info_list:
                    self.edges.append(Edge(start, end, info, self.init_phe))

    def reset_pheromone(self):
        for edge in self.edges:
            edge.pheromone = self.init_phe


class Ant:
    def __init__(self, world, s_index, alpha, betha):
        self.world = world
        self.alpha = alpha
        self.betha = betha
        self.start = (
            world.nodes[0] if s_index >= len(world.nodes) else world.nodes[s_index]
        )
        self.l_best = None

    def new_start(self, s_index):
        self.start = (
            self.world.nodes[0]
            if s_index >= len(self.world.nodes)
            else self.world.nodes[s_index]
        )

    def _candidates(self, pos):
        candidates = []
        for edge in self.world.edges:
            if (edge.end in self.unvisited) and (edge.start is pos):
                if len(self.unvisited) != 1 and (edge.end is self.start):
                    continue
                candidates.append(edge)
        return candidates

    def _choice(self, candidates):
        if self.world.h_func != None and self.betha != 0:
            h_probs = []
            p_probs = []

            for edge in candidates:
                h_probs.append(self.world.h_func(self.traveled, edge))
                p_probs.append(edge.pheromone)

            h_probs = np.array(h_probs)
            p_probs = np.array(p_probs)

            h_max = max(h_probs)
            h_min = min(h_probs)
            if h_max > h_min:
                h_probs = (h_max - h_probs) / (h_max - h_min)
            h_probs = h_probs / sum(h_probs)
            p_probs = p_probs / sum(p_probs)

            # Combine both probabilities using *alpha* and *betha*
            f_probs = (self.alpha * p_probs + self.betha * h_probs) / (
                self.alpha + self.betha
            )
        else:
            f_probs = []
            for edge in candidates:
                f_probs.append(edge.pheromone)
            f_probs = np.array(f_probs)
            f_probs = f_probs / sum(f_probs)

        # Select the edge to be traversed
        draw = random.random()
        roullete = 0
        for i in range(len(f_probs)):
            prob = f_probs[i]
            roullete += prob
            if draw < roullete:
                return candidates[i]
        return candidates[-1]

    def create_path(self):
        """
        Create the path traveled by the ant across the world.

        Details:
          Through this method an object from the class 'Ant' contructs a path in *traveled*.
          It is a possible solution comprising the traveled edges. The tour, visited nodes,
          is also stored, which is the attribute *visited*.
        """

        # Initialize path and tour variables.
        self.visited = []
        self.traveled = []
        self.unvisited = self.world.nodes.copy()
        pos = self.start

        while True:
            # List the possible movements from the current position.
            candidates = self._candidates(pos)

            # Select a movement.
            choice = self._choice(candidates)

            # Make the selected movement (traverse the edge).
            self.traveled.append(choice)

            # Mark the end node of the traversed edge as visited.
            self.unvisited.remove(choice.end)
            self.visited.append(choice.end)

            if len(self.unvisited) == 225:
                # Conclude the path and return its cost.
                cost = self.world.c_func(self.traveled)
                if self.l_best is None:
                    self.l_best = (cost, self.visited, self.traveled)
                elif cost[0][1][3]["pressure"] < self.l_best[0][0][1][3]["pressure"]:
                    self.l_best = (cost, self.visited, self.traveled)
                return cost
            else:
                # Update the current position
                pos = self.visited[-1]

    def pheromone_update(self, phe_dep):
        """
        Update the pheromone deposited across the path.

        Details:
          Each traveled edge receives an addition to the deposited pheromone.
          This addition is equal to the parameter phe_dep.

        Parameters:
          * phe_dep: value to be added to the pheromone deposit.
        """
        for edge in self.traveled:
            edge.pheromone += phe_dep


class AntSystem:
    def __init__(
        self,
        world,
        n_ants,
        rand_start=True,
        alpha=1,
        betha=3,
        phe_dep=1,
        evap_rate=0.2,
        elite_p_ants=0.3,
        phe_dep_elite=1,
    ):
        self.world = world
        self.evap_rate = evap_rate
        self.n_ants = n_ants
        self.rand_start = rand_start
        self.alpha = alpha
        self.betha = betha
        self.phe_dep = phe_dep
        self.elite_p_ants = elite_p_ants
        self.phe_dep_elite = phe_dep_elite
        self.g_best = None
        self.cost_history = []

        self.start_colony()

    def start_colony(self):
        self.ants = []
        limit = len(self.world.nodes) - 1

        for ant in range(self.n_ants):
            s_index = random.randint(0, limit) if self.rand_start else 0
            self.ants.append(Ant(self.world, s_index, self.alpha, self.betha))

    def optimize(self, max_iter=50, n_iter_no_change=10, verbose=True):
        count = 0

        s_iter = len(self.cost_history) + 1
        f_iter = s_iter + max_iter

        for iter in range(s_iter, f_iter):
            ants = []
            for ant in self.ants:
                cost = ant.create_path()

                ant.pheromone_update(self.phe_dep)

                ants.append((cost, ant))
                print("ant: " + str(len(ants)))

            def sort_cost(e):
                return e[0][0][1][3]["pressure"]

            ants.sort(key=sort_cost)

            n_elite_ants = round(self.elite_p_ants * len(ants))

            for i in range(n_elite_ants):
                ants[i][1].pheromone_update(self.phe_dep_elite)

            for edge in self.world.edges:
                edge.pheromone *= 1 - self.evap_rate
            print("----------- [ teste ] -----------")
            print(ants[0][0][0][1][3]["pressure"])
            if self.g_best is not None:
                print(self.g_best[0][0][1][3]["pressure"])
                print("----------- [ teste ] -----------")
            if self.g_best is None:
                self.g_best = (ants[0][0], ants[0][1].visited, ants[0][1].traveled)
            elif ants[0][0][0][1][3]["pressure"] < self.g_best[0][0][1][3]["pressure"]:
                count = 0
                self.g_best = (ants[0][0], ants[0][1].visited, ants[0][1].traveled)
            else:
                count += 1

            if ants[0][0] is not None:
                self.cost_history.append(self.g_best[0][0][1][3]["pressure"])

            if verbose:
                if self.g_best[0][0][1][3]["pressure"] == 0:
                    print(
                        "\033[31m O valores de pressão não atendem as faixas de mínimo e máximo \033[m"
                    )
                else:
                    print("\n" * 3)
                    print(
                        "| iter |         min        |         max        |        best        |"
                    )
                    print(
                        "|%6i|%20g|%20g|%20g|"
                        % (
                            iter,
                            ants[0][0][0][1][3]["pressure"],
                            ants[-1][0][0][1][3]["pressure"],
                            self.g_best[0][0][1][3]["pressure"],
                        )
                    )
                    print("\n" * 3)
                    print("Configuração das valvulas")
                    print(ants[-1][0])
                    print("\n" * 5)

            if count >= n_iter_no_change:
                break
