import networkx as nx

from state import State

from mesa import Model, Agent
from mesa.time import RandomActivation
from mesa.datacollection import DataCollector
from mesa.space import NetworkGrid

import math


def number_state(model, state):
    return sum([1 for a in model.grid.get_all_cell_contents() if a.state is state])


def number_susceptible(model):
    return number_state(model, State.SUSCEPTIBLE)


def number_interested(model):
    return number_state(model, State.INTERESTED)


def number_bored(model):
    return number_state(model, State.BORED)


class MemeModel(Model):
    """
    A meme model with a number of agents.
    The model will run on a graph environment.
    """

    def __init__(
        self,
        num_nodes=100,
        n_groups=2,
        initial_viral_size=10,
        meme_spread_chance=0.4,
        maybe_bored=0.3
    ) -> None:
        # init model variables
        self.num_nodes = num_nodes
        node_list = [num_nodes // n_groups for _ in range(n_groups)]
        node_list[-1] += num_nodes - sum(node_list)  # adding odd nodes to last group
        p_in = 0.01
        p_out = 0.05
        self.G = nx.random_partition_graph(node_list, p_in, p_out)
        self.grid = NetworkGrid(self.G)
        self.schedule = RandomActivation(self)
        self.initial_viral_size = (
            initial_viral_size if initial_viral_size <= num_nodes else num_nodes
        )
        self.meme_spread_chance = meme_spread_chance
        self.maybe_bored = maybe_bored

        self.datacollector = DataCollector(
            {
                "Susceptible": number_susceptible,
                "Interested": number_interested,
                "Bored": number_bored
            }
        )

        # create agents
        for i, node in enumerate(self.G.nodes()):
            a = MemeAgent(
                i,
                self,
                State.SUSCEPTIBLE,
                self.meme_spread_chance,
                self.maybe_bored
            )
            self.schedule.add(a)
            # add the agent to the node
            self.grid.place_agent(a, node)

        # some nodes are already interested in a meme
        interested_nodes = self.random.sample(self.G.nodes(), self.initial_viral_size)
        for a in self.grid.get_cell_list_contents(interested_nodes):
            a.state = State.INTERESTED

        self.running = True
        self.datacollector.collect(self)

    def bored_susceptible_ratio(self):
        try:
            return number_state(self, State.BORED) / number_state(
                self, State.SUSCEPTIBLE
            )
        except ZeroDivisionError:
            return math.inf

    def step(self):
        self.schedule.step()
        # collect data
        self.datacollector.collect(self)

    def run_model(self, n):
        for i in range(n):
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

    def try_to_spread_memes(self):
        neighbors_nodes = self.model.grid.get_neighbors(self.pos, include_center=False)
        susceptible_neighbors = [
            agent for agent in self.model.grid.get_cell_list_contents(neighbors_nodes)
            if agent.state is State.SUSCEPTIBLE
        ]
        for a in susceptible_neighbors:
            if self.random.random() < self.meme_spread_chance:
                a.state = State.INTERESTED

    def try_be_bored(self):
        if self.random.random() < self.maybe_bored:
            self.state = State.BORED
        # else:
        #     self.state = State.INTERESTED

    def step(self):
        if self.state is State.INTERESTED:
            self.try_to_spread_memes()
            self.try_be_bored()
        if not State.BORED:
            self.try_be_bored()
