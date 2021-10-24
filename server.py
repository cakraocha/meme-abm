from mesa.visualization.ModularVisualization import ModularServer
from mesa.visualization.UserParam import UserSettableParameter
from mesa.visualization.modules import ChartModule
from mesa.visualization.modules import NetworkModule
from mesa.visualization.modules import TextElement
from model import MemeModel, number_interested_B, number_interested_A
from state import State

import math


def network_portrayal(G):
    # the model ensures there is always 1 agent per node

    def node_color(agent):
        if State.SUSCEPTIBLE in agent.state:
            return "#3CB043"
        if State.INTERESTED_A in agent.state and State.INTERESTED_B in agent.state:
            return "#710193"
        if State.INTERESTED_A in agent.state:
            return "#E3242B"
        if State.INTERESTED_B in agent.state:
            return "#3944BC"
        if State.BORED_A in agent.state and State.BORED_B in agent.state:
            return "#212121"
        if State.BORED_A in agent.state:
            return "#4E0707"
        if State.BORED_B in agent.state:
            return "#0A1172"
        # return {
        #     State.SUSCEPTIBLE: "#3CB043", State.INTERESTED: "#E3242B"
        # }.get(agent.state, "#808080")

    def edge_color(agent1, agent2):
        # if State.BORED in (agent1.state, agent2.state):
        #     return "#000000"
        if (State.INTERESTED_A in agent1.state and State.INTERESTED_B in agent1.state) \
            or (State.INTERESTED_A in agent2.state and State.INTERESTED_B in agent2.state):
            return "#710193"
        if State.INTERESTED_A in agent1.state or State.INTERESTED_A in agent2.state:
            return "#D21404"
        if State.INTERESTED_B in agent1.state or State.INTERESTED_B in agent2.state:
            return "#1338BE"
        return "#E8E8E8"

    def edge_width(agent1, agent2):
        # if State.BORED in (agent1.state, agent2.state):
        #     return 3
        return 2

    def get_agents(source, target):
        return G.nodes[source]["agent"][0], G.nodes[target]["agent"][0]

    portrayal = {}
    portrayal["nodes"] = [
        {
            "size": 6,
            "color": node_color(agents[0]),
            "tooltip": "id: {}<br>state: {}".format(
                agents[0].unique_id, [s.name for s in agents[0].state]
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
        {"Label": "Interested_A", "Color": "#E3242B"},
        {"Label": "Interested_B", "Color": "#3944BC"},
        {"Label": "Interested_both", "Color": "#710193"},
        {"Label": "Bored_A", "Color": "#4E0707"},
        {"Label": "Bored_B", "Color": "#0A1172"},
        {"Label": "Bored_both", "Color": "#212121"}
    ]
)


class MyTextElement(TextElement):
    def render(self, model):
        # ratio = model.bored_susceptible_ratio()
        # ratio_text = "&infin;" if ratio is math.inf else "{0:2f}".format(ratio)
        interested_A_text = str(number_interested_A(model))
        interested_B_text = str(number_interested_B(model))

        return "Interested A remaining: {}<br>Interested B remaining: {}".format(
            interested_A_text, interested_B_text
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
    "n_groups": UserSettableParameter(
        "slider",
        "Number of Groups",
        2,
        2,
        10,
        1,
        description="Set your group partition",
    ),
    "initial_viral_size_A": UserSettableParameter(
        "slider",
        "Initial viral size A",
        5,
        5,
        50,
        1,
        description="Viral size determine the number of interested nodes for meme A",
    ),
    "initial_viral_size_B": UserSettableParameter(
        "slider",
        "Initial viral size B",
        5,
        5,
        50,
        1,
        description="Viral size determine the number of interested nodes for meme B",
    ),
    "meme_A_spread_chance": UserSettableParameter(
        "slider",
        "Meme A spread chance",
        0.3,
        0.0,
        1.0,
        0.1,
        description="Probability for 'Meme A' in spreading to another node",
    ),
    "meme_B_spread_chance": UserSettableParameter(
        "slider",
        "Meme B spread chance",
        0.3,
        0.0,
        1.0,
        0.1,
        description="Probability for 'Meme B' in spreading to another node",
    ),
    "maybe_bored_A": UserSettableParameter(
        "slider",
        "Become bored Meme A chance",
        0.3,
        0.0,
        1.0,
        0.1,
        description="Probability that a node become bored of 'Meme A' and not spread meme",
    ),
    "maybe_bored_B": UserSettableParameter(
        "slider",
        "Become bored Meme B chance",
        0.3,
        0.0,
        1.0,
        0.1,
        description="Probability that a node become bored of 'Meme B' and not spread meme",
    ),
}


server = ModularServer(
    MemeModel, [network, MyTextElement(), chart], "Meme Model", model_params
)

server.port = 8521
