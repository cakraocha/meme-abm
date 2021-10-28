from state import State

from mesa import Agent

class MemeAgent(Agent):
    """
    Internet meme agent that consume and spread memes.

    :param unique_id: *int*
        The id assigned to a node.
        Id must be unique

    :param model: *MemeModel*
        The model used for the agent to live.

    :param initial_state: *set*
        A set of State for identifying the node's state.

    :param meme_spread_chance: *float*
        The base probability of a meme to spread to other nodes.

    :param maybe_bored: *float*
        The base probability of a node to be bored of a meme.

    :param meme_interest_A: *float*
        The discount value for spread chance of Meme A.

    :param meme_interest_B: *float*
        The discount value for spread chance of Meme B.
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
        super().__init__(unique_id, model)

        self.state = initial_state

        # apply discount factor to either influencer or ordinary node
        if State.INFLUENCER in initial_state:
            self.meme_A_spread_chance = influencer_spread_chance * meme_interest_A
            self.meme_B_spread_chance = influencer_spread_chance * meme_interest_B
        else:
            self.meme_A_spread_chance = meme_spread_chance * meme_interest_A
            self.meme_B_spread_chance = meme_spread_chance * meme_interest_B
        self.maybe_bored_A = maybe_bored
        self.maybe_bored_B = maybe_bored

        # we set a time before an agent change state
        # for now, we set the time into fixed time
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

        # check first for state in which category of meme does a node interested in
        if state is State.INTERESTED_A:
            for a in neighbors_contents:
                # neighbour node will be interested after certain time past
                if self.TIME_BEFORE_INTERESTED_A > 0:
                    self.deduct_before_interest_A()
                if self.random.random() < self.meme_A_spread_chance:
                    if self.TIME_BEFORE_INTERESTED_A == 0:
                        if State.SUSCEPTIBLE in a.state:
                            a.state.remove(State.SUSCEPTIBLE)
                        a.state.add(State.INTERESTED_A)
        # same with logic above
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
        """
        A method for the agent to be bored of a meme
        """
        # no agents will be bored before specified time
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
        """
        The actions for the agent to take for each step/tick
        depending on the state.
        """
        if State.INTERESTED_A in self.state:
            self.try_to_spread_memes(State.INTERESTED_A)
            self.try_be_bored(State.INTERESTED_A)
        if State.INTERESTED_B in self.state:
            self.try_to_spread_memes(State.INTERESTED_B)
            self.try_be_bored(State.INTERESTED_B)
