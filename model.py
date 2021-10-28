import networkx as nx

from state import State

from mesa import Model, Agent
from mesa.time import RandomActivation
from mesa.datacollection import DataCollector
from mesa.space import NetworkGrid


#############################
# FUNCTIONS TO COLLECT DATA #
#############################


def number_state(model, state):
    return sum([1 for a in model.grid.get_all_cell_contents() if state in a.state])


def number_state_dual(model, state1, state2):
    return sum([
        1 for a in model.grid.get_all_cell_contents()
        if state1 in a.state and state2 in a.state
    ])


def number_steps(model):
    return model.step_counter


def number_peak_meme_A(model):
    return model.get_peak_meme_A()


def number_peak_meme_B(model):
    return model.get_peak_meme_B()


def step_peak_meme_A(model):
    return model.get_step_peak_meme_A()


def step_peak_meme_B(model):
    return model.get_step_peak_meme_B()


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


def number_interest_A(model):
    return number_state(model, State.INTEREST_A)


def number_interest_B(model):
    return number_state(model, State.INTEREST_B)


def number_interest_both(model):
    return number_state_dual(model, State.INTEREST_A, State.INTEREST_B)


####################################
# END OF COLLECTING DATA FUNCTIONS #
####################################


class MemeModel(Model):
    """
    A meme model with a number of agents.
    The model will run on a graph environment.

    :param num_nodes: *int*, default 100
        The number of nodes that will be simulated in the model.
        Range between 100 - 500 with 10 incremental.
    
    :param n_groups: *int*, default 2
        The number of groups that will divide the nodes.
        The number of nodes will be divided evenly with odd
        numbers will be added in the last group.
        e.g. 100 nodes with 3 groups makes [33, 33, 34].
    
    :param initial_viral_size_A: *int*, default 5
        The initial number of nodes that is interested to Meme A.
    
    :param initial_viral_size_B: *int*, default 5
        The initial number of nodes that is interested to Meme B.
    
    :param meme_spread_chance: *int*, default 0.3
        The base probability of a meme to spread to other nodes.
    
    :param maybe_bored: *int*, default 0.3
        The base probability of a node to be bored of a meme.
    
    :param influencer_appearance: *int*, default 1
        The number of influencer(s) in a given scenario.
    
    :param influencer_spread_chance: *int*, default 0.6
        The base probability of an influencer to spread meme to other nodes.
    
    :interest_meme_A_chance: *int*, default 0.5
        The probability of a node to develop interest to Meme A.
    
    :interest_meme_B_chance: *int*, default 0.5
        The probability of a node to develop interest to Meme B.
    
    """

    def __init__(
        self,
        num_nodes=100,
        n_groups=2,
        initial_viral_size_A=5,
        initial_viral_size_B=5,
        meme_spread_chance=0.3,
        maybe_bored=0.3,
        influencer_appearance=1,
        influencer_spread_chance=0.6,
        interest_meme_A_chance=0.5,
        interest_meme_B_chance=0.5
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
        self.influencer_appearance = influencer_appearance
        self.influencer_spread_chance = influencer_spread_chance

        self.datacollector = DataCollector(
            {
                "Susceptible": number_susceptible,
                "Interested_A": number_interested_A,
                "Interested_B": number_interested_B,
                "Interested_both": number_interested_both,
                "Bored_A": number_bored_A,
                "Bored_B": number_bored_B,
                "Bored_both": number_bored_both,
                "Interest_A": number_interest_A,
                "Interest_B": number_interest_B,
                "Interest_both": number_interest_both
            }
        )

        # probability used in determining user interest
        # TODO: make parameterised
        self.interest_meme_A_chance = interest_meme_A_chance
        self.interest_meme_B_chance = interest_meme_B_chance

        # recording peak interest in meme
        self.peak_meme_A = 0
        self.peak_meme_B = 0
        self.step_counter = 0
        self.step_meme_A = 0
        self.step_meme_B = 0

        # create agents
        for i, node in enumerate(self.G.nodes()):
            state = {State.SUSCEPTIBLE}
            # we determine the discount value for each agent interest
            if self.random.random() < self.interest_meme_A_chance:
                interest_A = 0.95
                state.add(State.INTEREST_A)
            else:
                interest_A = 0.1
            if self.random.random() < self.interest_meme_B_chance:
                interest_B = 0.95
                state.add(State.INTEREST_B)
            else:
                interest_B = 0.1
            a = MemeAgent(
                    i,
                    self,
                    state,
                    self.meme_spread_chance,
                    self.maybe_bored,
                    interest_A,
                    interest_B,
                    self.influencer_spread_chance
                )
            self.schedule.add(a)
            # add the agent to the node
            self.grid.place_agent(a, node)

        # initiate influencer in the nodes
        # TODO: find a way to sample nodes with certain edges
        influencer_nodes = self.random.sample(self.G.nodes(), self.influencer_appearance)
        influencers = self.grid.get_cell_list_contents(influencer_nodes)
        for inf in influencers:
            inf.state.add(State.INFLUENCER)

        # some nodes are already interested in a meme depending on viral size
        interested_nodes_A = self.random.sample(self.G.nodes(), self.initial_viral_size_A)
        agents_A = self.grid.get_cell_list_contents(interested_nodes_A)
        interested_nodes_B = self.random.sample(self.G.nodes(), self.initial_viral_size_B)
        agents_B = self.grid.get_cell_list_contents(interested_nodes_B)
        for aa in agents_A:
            aa.state.add(State.INTERESTED_A)
            if State.INTEREST_A not in aa.state:
                aa.state.add(State.INTEREST_A)
            if State.SUSCEPTIBLE in aa.state:
                aa.state.remove(State.SUSCEPTIBLE)
        for ab in agents_B:
            ab.state.add(State.INTERESTED_B)
            if State.INTEREST_B not in ab.state:
                ab.state.add(State.INTEREST_B)
            if State.SUSCEPTIBLE in ab.state:
                ab.state.remove(State.SUSCEPTIBLE)

        self.running = True
        self.datacollector.collect(self)

    def step(self):
        self.schedule.step()
        self.step_counter += 1
        # collect data
        self.datacollector.collect(self)
        # recording number of peak interested in a meme with step n
        if number_interested_A(self) > self.peak_meme_A:
            self.peak_meme_A = number_interested_A(self)
            self.step_meme_A = self.step_counter
        if number_interested_B(self) > self.peak_meme_B:
            self.peak_meme_B = number_interested_B(self)
            self.step_meme_B = self.step_counter
        # stop condition is when no one is actively spreading the meme
        if number_interested_A(self) + number_interested_B(self) == 0:
            self.running = False

    def get_peak_meme_A(self):
        return self.peak_meme_A

    def get_peak_meme_B(self):
        return self.peak_meme_B

    def get_step_peak_meme_A(self):
        return self.step_meme_A

    def get_step_peak_meme_B(self):
        return self.step_meme_B


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
        maybe_bored,
        meme_interest_A,
        meme_interest_B,
        influencer_spread_chance
    ):
        """
        Initiate a new meme agent.
        """
        super().__init__(unique_id, model)

        self.state = initial_state

        if State.INFLUENCER in initial_state:
            self.meme_A_spread_chance = influencer_spread_chance * meme_interest_A
            self.meme_B_spread_chance = influencer_spread_chance * meme_interest_B
        else:
            self.meme_A_spread_chance = meme_spread_chance * meme_interest_A
            self.meme_B_spread_chance = meme_spread_chance * meme_interest_B
        self.maybe_bored_A = maybe_bored
        self.maybe_bored_B = maybe_bored

        # we set a time before an agent change state
        # for now, we set the time into 2
        self.TIME_BEFORE_INTERESTED_A = self.random.randrange(1, 2, 1)
        self.TIME_BEFORE_INTERESTED_B = self.random.randrange(1, 2, 1)
        self.TIME_BEFORE_BORED_A = self.random.randrange(2, 4, 1)
        self.TIME_BEFORE_BORED_B = self.random.randrange(2, 4, 1)


    def deduct_before_interest_A(self):
        self.TIME_BEFORE_INTERESTED_A -= 1

    def deduct_before_bored_A(self):
        self.TIME_BEFORE_BORED_A -= 1

    def deduct_before_interest_B(self):
        self.TIME_BEFORE_INTERESTED_B -= 1

    def deduct_before_bored_B(self):
        self.TIME_BEFORE_BORED_B -= 1

    def try_to_spread_memes(self, state):
        """
        A method for agent to spread memes.
        """
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
                if self.TIME_BEFORE_INTERESTED_A > 0:
                    self.deduct_before_interest_A()
                if self.random.random() < self.meme_A_spread_chance:
                    if self.TIME_BEFORE_INTERESTED_A == 0:
                        if State.SUSCEPTIBLE in a.state:
                            a.state.remove(State.SUSCEPTIBLE)
                        a.state.add(State.INTERESTED_A)
        elif state is State.INTERESTED_B:
            for a in neighbors_contents:
                if self.TIME_BEFORE_INTERESTED_B > 0:
                    self.deduct_before_interest_B()
                if self.random.random() < self.meme_B_spread_chance:
                    if self.TIME_BEFORE_INTERESTED_B == 0:
                        if State.SUSCEPTIBLE in a.state:
                            a.state.remove(State.SUSCEPTIBLE)
                        a.state.add(State.INTERESTED_B)

    def try_be_bored(self, state):
        if state is State.INTERESTED_A and self.TIME_BEFORE_BORED_A > 0:
            self.deduct_before_bored_A()
        elif state is State.INTERESTED_B and self.TIME_BEFORE_BORED_B > 0:
            self.deduct_before_bored_B()
        bored_random = self.random.random()
        if state is State.INTERESTED_A and bored_random < self.maybe_bored_A:
            if self.TIME_BEFORE_BORED_A == 0:
                self.state.remove(State.INTERESTED_A)
                self.state.add(State.BORED_A)
        if state is State.INTERESTED_B and bored_random < self.maybe_bored_B:
            if self.TIME_BEFORE_BORED_B == 0:
                self.state.remove(State.INTERESTED_B)
                self.state.add(State.BORED_B)

    def step(self):
        if State.INTERESTED_A in self.state:
            self.try_to_spread_memes(State.INTERESTED_A)
            self.try_be_bored(State.INTERESTED_A)
        if State.INTERESTED_B in self.state:
            self.try_to_spread_memes(State.INTERESTED_B)
            self.try_be_bored(State.INTERESTED_B)
