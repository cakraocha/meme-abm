from enum import Enum
import networkx as nx

from mesa import Model, Agent
from mesa.time import RandomActivation
from mesa.space import NetworkGrid


class MemeAgent(Agent):
    """
    Internet meme agent that consume and spread memes.
    """


    def __init__(self, pos, model, agent_type):
        """
        Initiate a new meme agent.
        """
        super().__init__(pos, model)
        self.pos = pos
        self.type = agent_type


    def step(self):
