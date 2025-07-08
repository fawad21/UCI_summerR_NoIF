"""
biring.py – simple clockwise bidrectional ring topology for Ruby/Garnet
refrence:https://gem5bootcamp.github.io/2024/#03-Developing-gem5-models/08-ruby-network

"""

from topologies.BaseTopology import BaseTopology
from m5.objects import *


class biring(BaseTopology):
    description= "clockwise bidirectional ring"

    def __init___init_(self, controller):
        super().__init__()
        self.nodes = controllers

    def makeTopology(self, options, network, IntLink, ExtLink, Router):

        link_lat = options.link_latency
        router_lat = options.router_latency

























