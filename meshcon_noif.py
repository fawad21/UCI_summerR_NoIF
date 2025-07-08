"""
meshcon_noif.py - FD/UD cross connected mesh topology



Refrence: https://ieeexplore.ieee.org/stamp/stamp.jsp?tp=&arnumber=8771326
"""

from topologies.BaseTopology import BaseTopology
from m5.objects   import *

class meshcon_noif(BaseTopology):
    description="Bidirectional FD/UD cross-mesh (13 routers)"

    def __init__(self, controllers):
        super().__init__()
        assert len(controllers) == 13, "implementing only 13 controllers"
        self.nodes = controllers              