from simulation import Simulation
from constants import Constants
import random
from particle import Particle
import cProfile
import pstats


def runSimulation():
    simulation = Simulation.get_instance()
    
    for _ in range(400):
        particle = Particle(random.uniform(0.0, Constants.SCREEN_WIDTH), random.uniform(0.0, Constants.SCREEN_HEIGHT))
        Constants.PARTICLES.add(particle)


    simulation.run()
    
    

    
if __name__ == "__main__":
    cProfile.run('runSimulation()', "funcStats")
    
    p = pstats.Stats("funcStats")
    p.sort_stats("cumulative").print_stats()







