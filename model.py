import networkx as nx

from state import State

from mesa import Model, Agent
from mesa.time import RandomActivation
from mesa.datacollection import DataCollector
from mesa.space import NetworkGrid

import math


def number_state(model, state):
    return sum([1 for a in model.grid.get_all_cell_contents() if state in a.state])


def number_state_dual(model, state1, state2):
    return sum([
        1 for a in model.grid.get_all_cell_contents()
        if state1 in a.state and state2 in a.state
    ])


def number_susceptible(model):
    return number_state(model, State.SUSCEPTIBLE)


def number_interested_A(model):
    return number_state(model, State.INTERESTED_A)


def number_interested_B(model):
    return number_state(model, State.INTERESTED_B)


def number_interested_both(model):
    return number_state_dual(model, State.INTERESTED_A, State.INTERESTED_B)


def number_bored_A(model):
    return number_state(model, State.BORED_A)


def number_bored_B(model):
    return number_state(model, State.BORED_B)


def number_bored_both(model):
    return number_state_dual(model, State.BORED_A, State.BORED_B)


class MemeModel(Model):
    """
    A meme model with a number of agents.
    The model will run on a graph environment.
    """

    def __init__(
        self,
        num_nodes=100,
        n_groups=2,
        initial_viral_size_A=1,
        initial_viral_size_B=1,
        meme_spread_chance=0.3,
        maybe_bored=0.3
    ) -> None:
        # init model variables
        self.num_nodes = num_nodes
        node_list = [num_nodes // n_groups for _ in range(n_groups)]
        node_list[-1] += num_nodes - sum(node_list)  # adding odd nodes to last group
        p_in = 0.08
        p_out = 0.003
        self.G = nx.random_partition_graph(node_list, p_in, p_out)
        self.grid = NetworkGrid(self.G)
        self.schedule = RandomActivation(self)
        self.initial_viral_size_A = (
            initial_viral_size_A if initial_viral_size_A <= num_nodes else num_nodes
        )
        self.initial_viral_size_B = (
            initial_viral_size_B if initial_viral_size_B <= num_nodes else num_nodes
        )
        self.meme_spread_chance = meme_spread_chance
        self.maybe_bored = maybe_bored

        self.datacollector = DataCollector(
            {
                "Susceptible": number_susceptible,
                "Interested_A": number_interested_A,
                "Interested_B": number_interested_B,
                "Interested_both": number_interested_both,
                "Bored_A": number_bored_A,
                "Bored_B": number_bored_B,
                "Bored_both": number_bored_both,
            }
        )

        # create agents
        for i, node in enumerate(self.G.nodes()):
            a = MemeAgent(
                i,
                self,
                {State.SUSCEPTIBLE},
                self.meme_spread_chance,
                self.maybe_bored
            )
            self.schedule.add(a)
            # add the agent to the node
            self.grid.place_agent(a, node)

        # some nodes are already interested in a meme
        interested_nodes_A = self.random.sample(self.G.nodes(), self.initial_viral_size_A)
        agents_A = self.grid.get_cell_list_contents(interested_nodes_A)
        interested_nodes_B = self.random.sample(self.G.nodes(), self.initial_viral_size_B)
        agents_B = self.grid.get_cell_list_contents(interested_nodes_B)
        for aa in agents_A:
            aa.state.add(State.INTERESTED_A)
            if State.SUSCEPTIBLE in aa.state:
                aa.state.remove(State.SUSCEPTIBLE)
        for ab in agents_B:
            ab.state.add(State.INTERESTED_B)
            if State.SUSCEPTIBLE in ab.state:
                ab.state.remove(State.SUSCEPTIBLE)

        self.running = True
        self.datacollector.collect(self)

    def set_running(self, bool):
        self.running = bool

    # def bored_susceptible_ratio(self):
    #     try:
    #         return number_state(self, State.BORED) / number_state(
    #             self, State.SUSCEPTIBLE
    #         )
    #     except ZeroDivisionError:
    #         return math.inf

    def step(self):
        self.schedule.step()
        # collect data
        self.datacollector.collect(self)

    # def run_model(self):
    #     while self.running:
    #         if number_state(self, State.INTERESTED) == 0:
    #             self.set_running(False)
    #             break
    #         self.step()

    def run_model(self, n):
        for _ in range(n):
            # if number_state(self, State.INTERESTED) == 0:
            #     self.set_running(False)
            #     break
            self.step()


class MemeAgent(Agent):
    """
    Internet meme agent that consume and spread memes.
    """


    def __init__(
        self,
        unique_id,
        model,
        initial_state,
        meme_spread_chance,
        maybe_bored
    ):
        """
        Initiate a new meme agent.
        """
        super().__init__(unique_id, model)

        self.state = initial_state

        self.meme_spread_chance = meme_spread_chance
        self.maybe_bored = maybe_bored

    def try_to_spread_memes(self, state):
        neighbors_nodes = self.model.grid.get_neighbors(self.pos, include_center=False)
        neighbors_contents = [
            agent for agent in self.model.grid.get_cell_list_contents(neighbors_nodes)
            if State.BORED_A not in agent.state and State.BORED_B not in agent.state
        ]
        # susceptible_neighbors = [
        #     agent for agent in self.model.grid.get_cell_list_contents(neighbors_nodes)
        #     if State.SUSCEPTIBLE in agent.state
        # ]
        if state is State.INTERESTED_A:
            for a in neighbors_contents:
                if self.random.random() < self.meme_spread_chance:
                    if State.SUSCEPTIBLE in a.state:
                        a.state.remove(State.SUSCEPTIBLE)
                    a.state.add(State.INTERESTED_A)
        elif state is State.INTERESTED_B:
            for a in neighbors_contents:
                if self.random.random() < self.meme_spread_chance:
                    if State.SUSCEPTIBLE in a.state:
                        a.state.remove(State.SUSCEPTIBLE)
                    a.state.add(State.INTERESTED_B)

    def try_be_bored(self, state):
        bored_random = self.random.random()
        if state is State.INTERESTED_A and bored_random < self.maybe_bored:
            self.state.remove(State.INTERESTED_A)
            self.state.add(State.BORED_A)
        if state is State.INTERESTED_B and bored_random < self.maybe_bored:
            self.state.remove(State.INTERESTED_B)
            self.state.add(State.BORED_B)

    def step(self):
        if State.INTERESTED_A in self.state:
            self.try_to_spread_memes(State.INTERESTED_A)
            self.try_be_bored(State.INTERESTED_A)
        if State.INTERESTED_B in self.state:
            self.try_to_spread_memes(State.INTERESTED_B)
            self.try_be_bored(State.INTERESTED_B)
        
