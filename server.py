from mesa.visualization.ModularVisualization import ModularServer
from mesa.visualization.UserParam import UserSettableParameter
from mesa.visualization.modules import ChartModule
from mesa.visualization.modules import NetworkModule
from mesa.visualization.modules import TextElement
from model import MemeModel, number_interested
from state import State

import math


def network_portrayal(G):
    # the model ensures there is always 1 agent per node

    def node_color(agent):
        return {
            State.SUSCEPTIBLE: "#3CB043", State.INTERESTED: "#E3242B"
        }.get(agent.state, "#808080")

    def edge_color(agent1, agent2):
        if State.BORED in (agent1.state, agent2.state):
            return "#000000"
        return "#e8e8e8"

    def edge_width(agent1, agent2):
        if State.BORED in (agent1.state, agent2.state):
            return 3
        return 2

    def get_agents(source, target):
        return G.nodes[source]["agent"][0], G.nodes[target]["agent"][0]

    portrayal = {}
    portrayal["nodes"] = [
        {
            "size": 6,
            "color": node_color(agents[0]),
            "tooltip": "id: {}<br>state: {}".format(
                agents[0].unique_id, agents[0].state.name
            ),
        }
        for (_, agents) in G.nodes.data("agent")
    ]

    portrayal["edges"] = [
        {
            "source": source,
            "target": target,
            "color": edge_color(*get_agents(source, target)),
            "width": edge_width(*get_agents(source, target)),
        }
        for (source, target) in G.edges
    ]

    return portrayal

network = NetworkModule(network_portrayal, 500, 500, library="d3")
chart = ChartModule(
    [
        {"Label": "Susceptible", "Color": "#3CB043"},
        {"Label": "Interested", "Color": "#E3242B"},
        {"Label": "Bored", "Color": "#808080"},
    ]
)


class MyTextElement(TextElement):
    def render(self, model):
        ratio = model.bored_susceptible_ratio()
        ratio_text = "&infin;" if ratio is math.inf else "{0:2f}".format(ratio)
        interested_text = str(number_interested(model))

        return "Bored/Susceptible Ratio: {}<br>Interested remaining: {}".format(
            ratio_text, interested_text
        )


model_params = {
    "num_nodes": UserSettableParameter(
        "slider",
        "Number of agents",
        100,
        100,
        500,
        10,
        description="How many agents to be included in the model?",
    ),
    "avg_node_degree": UserSettableParameter(
        "slider", "Avg Node Degree", 10, 10, 50, 1, description="Avg node degree"
    ),
    "initial_viral_size": UserSettableParameter(
        "slider",
        "Initial viral size",
        10,
        10,
        50,
        1,
        description="Viral size determine the number of interested nodes",
    ),
    "meme_spread_chance": UserSettableParameter(
        "slider",
        "Meme spread chance",
        0.4,
        0.0,
        1.0,
        0.1,
        description="Probability that a meme will spread to another node",
    ),
    "maybe_bored": UserSettableParameter(
        "slider",
        "Become bored chance",
        0.3,
        0.0,
        1.0,
        0.1,
        description="Probability that a node become bored and not spread meme",
    ),
}


server = ModularServer(
    MemeModel, [network, MyTextElement(), chart], "Meme Model", model_params
)

server.port = 8521
