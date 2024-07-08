from enum import Enum
import pygame
import time
from collections import defaultdict

class Constants:
    DEVELOPER = True
    MONITOR_INTERVAL = 5
    BLACK = (0, 0, 0)
    GREEN = (30, 150, 90)
    SCREEN_WIDTH = None
    SCREEN_HEIGHT = None
    TILE_WIDTH = None
    TILE_HEIGHT = None
    xCELLS = None
    yCELLS = None

    SCREEN = None
    BACKGROUND = None
    
    QUADTREE = None

    
    PARTICLES = set({})
    PARTICLE_NEIGHBORS = None
    
    
    # Setup double buffering
    PARTICLE_NEIGHBOR_VEL_BUFFERS = [defaultdict(list), defaultdict(list)]
    ACTIVE_BUFFER_INDEX = 0
    LAST_UPDATE_TIME = time.time()
    
    
    
    # @staticmethod
    # def batchQuery(particles, maxInfluenceDist):
    #     queryRanges = []
    #     results = {}
        
    #     for p in particles:
    #         rangeQuery = pygame.Rect(p.x - maxInfluenceDist, p.y - maxInfluenceDist, maxInfluenceDist * 2, maxInfluenceDist * 2)
    #         queryRanges.append((p, rangeQuery))
    #         results[p] = []
        
    #     for p, rangeQuery in queryRanges:
    #         found = Constants.QUADTREE.query(rangeQuery, [])
    #         results[p] = found
        
    #     return results
    
    SUPERCELL_SIZE = 80
    
    class displays(Enum):
        MAIN = 0
        SECONDARY = 1
        
    DISPLAY = displays.MAIN
    
        
    def calcCoords(x, y):
        x *= Constants.TILE_WIDTH
        y *= Constants.TILE_HEIGHT
        return (x, y)
    
    def calcCell(x, y):
        x = int(x // Constants.TILE_WIDTH)
        y = int(y // Constants.TILE_HEIGHT)
        return (x, y)
    
    def mapValue(input, inputMin, inputMax, outputMin, outputMax):
        return outputMin + ((input - inputMin) / (inputMax - inputMin)) * (outputMax - outputMin)
    
    
