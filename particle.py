import random
import pygame
import numpy as np
import math
import collections
from enum import Enum
from constants import Constants
from concurrent.futures import ThreadPoolExecutor
from threading import Lock
from collections import defaultdict
import time



class Particle():
    __particleAttractions = None
    MAX_INFLUENCE_DIST = 130
    MAX_INFLUENCE_DIST_x2 = MAX_INFLUENCE_DIST * 2
    MAX_INFLUENCE_DIST_SQUARED = MAX_INFLUENCE_DIST ** 2
    MIN_INFLUENCE_DIST = 5
    SPEED_LIMIT = 1

    def __init__(self, x, y):
        self.size = 2
        self.pos = np.array([x, y])
        self.vel = np.array([0.0, 0.0])
        self.setType()
        self.getParticleAttractions()


    def setType(self):
        pType = random.randint(0, len(self.particleTypes) - 1)
        self.particleType = self.particleTypeByIndex(pType)


    @staticmethod
    def getParticleAttractions():
        # Static method to get singleton instance
        # Create attraction table if it doesn't exist
        if Particle.__particleAttractions is None:
            Particle.__particleAttractions = {}
            
            # Initialize to list of 0's
            for p in Particle.particleTypes:
                Particle.__particleAttractions[p.name] = [0] * len(Particle.particleTypes)
            
            typesList = list(Particle.particleTypes)
            attractionMultiplier = 0.005
            for i, p in enumerate(typesList):
                for j in range (i, len(Particle.particleTypes)):
                    if i == j:
                        # Diagonals should be the same (similar particles should act the same)
                        Particle.__particleAttractions[p.name][j] = random.uniform(attractionMultiplier * -1, attractionMultiplier)
                    else:
                        value = random.uniform(attractionMultiplier * -1, attractionMultiplier)
                        Particle.__particleAttractions[p.name][j] = random.uniform(attractionMultiplier * -1, attractionMultiplier)
                        Particle.__particleAttractions[list(Particle.particleTypes)[j].name][i] = random.uniform(attractionMultiplier * -1, attractionMultiplier)
                        
        return Particle.__particleAttractions

    @staticmethod
    def updateVelocities(stopEvent):
        while not stopEvent.is_set():
            newBufferIndex = 1 - Constants.ACTIVE_BUFFER_INDEX
            newVels = defaultdict(lambda: np.zeros(2))
            
            def processParticle(p):
                
            # for p in Constants.PARTICLES:
                rangeQuery = pygame.Rect(
                    p.pos[0] - Particle.MAX_INFLUENCE_DIST,
                    p.pos[1] - Particle.MAX_INFLUENCE_DIST,
                    Particle.MAX_INFLUENCE_DIST_x2, 
                    Particle.MAX_INFLUENCE_DIST_x2
                )
                neighbors = Constants.QUADTREE.query(rangeQuery, [])
                
                neighborPositions = np.array([n.pos for n in neighbors if n != p])
                
                if len(neighborPositions) > 0:
                    deltas = neighborPositions - p.pos  # Vectorized subtraction
                    distances = np.linalg.norm(deltas, axis=1)
                    directions = deltas / distances[:, np.newaxis] # Normalize
                    
                    # print("nP: {}".format(neighborPositions))
                    # print("del: {}".format(deltas))
                    # print("dist: {}".format(distances))
                    # print("direct: {}".format(directions))
                    
                    # Ensure influences and forces calculation also uses NumPy operations
                    neighborInfluenceIndexes = [Particle.particleTypeByEnum(n.particleType) for n in neighbors if n != p]
                    influences = np.array([Particle.getParticleAttractions()[p.particleType.name][index] for index in neighborInfluenceIndexes])
                    
                    # forces = influences * np.exp(-distances / Particle.MAX_INFLUENCE_DIST)
                    
                    forces = np.zeros_like(distances)
                    
                    
                    # Split close particles into another object for a separate force function
                    closeDistances = distances < Particle.MIN_INFLUENCE_DIST
                    farDistances = ~closeDistances
                    
                    forces[closeDistances] = ((distances[closeDistances]) / Constants.PARTICLE_ATTRACTION_ALPHA) - 1
                    forces[farDistances] = Particle.MAX_INFLUENCE_DIST * influences[farDistances] * (1 - ((abs(2*(distances[farDistances] / Particle.MAX_INFLUENCE_DIST) - 1 - Constants.PARTICLE_ATTRACTION_BETA))/(1-Constants.PARTICLE_ATTRACTION_BETA)))
                    
                    forces = forces[:, np.newaxis]  # Reshape for broadcasting
                    
                    
                    totalForce = np.sum(forces * directions, axis=0)
                    # print("FORCE: {}".format(totalForce))
                    newVels[p] = totalForce
            
            
            with ThreadPoolExecutor() as executor:
                executor.map(processParticle, Constants.PARTICLES)
            
            Constants.PARTICLE_NEIGHBOR_VEL_BUFFERS[newBufferIndex] = newVels
            Constants.ACTIVE_BUFFER_INDEX = newBufferIndex
            # print("vels updated in {}".format(time.time() - Constants.LAST_UPDATE_TIME))
            Constants.LAST_UPDATE_TIME = time.time()
            
            time.sleep(0.01)
                    
                

    def update(self):
        self.calcVelocity()
        self.checkBoundaries()
        # self.speedLimit()
        self.move()
        self.draw()
        # Constants.QUADTREE.update(self)
        
        
    def checkBoundaries(self):
        if len(self.vel) == 0:
            return
        
        if self.pos[0] < 0:
            self.vel[0] = 0.05
        elif self.pos[0] > Constants.SCREEN_WIDTH:
            self.vel[0] = -0.05
            
        if self.pos[1] < 0:
            self.vel[1] = 0.05
        elif self.pos[1] > Constants.SCREEN_HEIGHT:
            self.vel[1] = -0.05
    
    def speedLimit(self):
        if len(self.vel) == 0:
            return
        
        if self.vel[0] > Particle.SPEED_LIMIT:
            self.vel[0] = Particle.SPEED_LIMIT
        elif self.vel[0] < Particle.SPEED_LIMIT * -1:
            self.vel[0] = Particle.SPEED_LIMIT * -1
            
        if self.vel[1] > Particle.SPEED_LIMIT:
            self.vel[1] = Particle.SPEED_LIMIT
        elif self.vel[1] < Particle.SPEED_LIMIT * -1:
            self.vel[1] = Particle.SPEED_LIMIT * -1
   
    def calcVelocity(self):
        self.vel = Constants.PARTICLE_NEIGHBOR_VEL_BUFFERS[Constants.ACTIVE_BUFFER_INDEX][self]
        

        # influenceTable = Particle.getParticleAttractions()
        
        # finalVelX, finalVelY = 0, 0
            
        # neighbors = Constants.PARTICLE_NEIGHBORS[self]
        # for p in neighbors:
            
        #     if p[1] != -1:
        #         dist = p[1]
        #     else:
        #         print("maybe shouldnt need this")
        #         dist = np.linalg.norm(p[0].pos - self.pos)
                
        #     if dist > Particle.MAX_INFLUENCE_DIST:
        #         continue
                
                
        #     influenceIndex = Particle.particleTypeByEnum(p[0].particleType)
        #     influence = influenceTable[p[0].particleType.name][influenceIndex]
                
        #     if influence > 0 and dist < Particle.MIN_INFLUENCE_DIST:
        #         impact = Particle.MIN_INFLUENCE_DIST - dist
        #         impact *= 0.4
        #         influence -= impact
                
        #     influence *= math.exp(-dist / Particle.MAX_INFLUENCE_DIST)
                
        #     if dist != 0:
        #         dirX = (self.pos[0] - p[0].pos[0]) / dist
        #         dirY = (self.pos[1] - p[0].pos[1]) / dist
                    
        #         finalVelX += influence * dirX
        #         finalVelY += influence * dirY
        
        # self.vel[0] = finalVelX
        # self.vel[1] = finalVelY


    def move(self):
        # If velocity hasn't been updated since program start, stay still
        if len(self.vel) == 0:
            return
        self.pos += self.vel



    
    def draw(self):
        pygame.draw.circle(Constants.SCREEN, self.particleType.value, (self.pos[0], self.pos[1]), self.size)

    
    @staticmethod
    def particleTypeByIndex(index):
        switch = {
            0: Particle.particleTypes.PINK,
            1: Particle.particleTypes.TEAL,
            2: Particle.particleTypes.GREY,
            3: Particle.particleTypes.MAIZE,
            4: Particle.particleTypes.INDIGO,
            5: Particle.particleTypes.ORANGE
        }
        return switch.get(index)

    @staticmethod
    def particleTypeByEnum(enum):
        switch = {
            Particle.particleTypes.PINK: 0,
            Particle.particleTypes.TEAL: 1,
            Particle.particleTypes.GREY: 2,
            Particle.particleTypes.MAIZE: 3,
            Particle.particleTypes.INDIGO: 4,
            Particle.particleTypes.ORANGE: 5,
        }
        return switch.get(enum)

    @staticmethod
    class particleTypes(Enum):
        PINK = (255, 130, 169)
        TEAL = (44, 175, 201)
        GREY = (156, 174, 169)
        MAIZE = (244, 224, 77)
        INDIGO = (84, 13, 110)
        ORANGE = (224, 92, 21)










 # def move(self):
    #     rangeQuery = pygame.Rect(self.x - (self.maxInfluenceDist/2), self.y - (self.maxInfluenceDist/2), self.maxInfluenceDist, self.maxInfluenceDist)
    #     closeParticles = Constants.QUADTREE.query(rangeQuery, [])

        
    #     finalVelX, finalVelY = 0, 0
        
            
        
    #     for p in closeParticles:
    #         dx = p.pos[0] - self.pos[0]
    #         dy = p.pos[1] - self.pos[1]
    #         distSquared = dx ** 2 + dy ** 2
                
    #         # Too far to impact particle
    #         # if distSquared > self.maxInfluenceDistSquared:
    #         #     continue
                
    #         dist = math.sqrt(distSquared)
                
                
    #             influenceIndex = particle.particleTypeByEnum(p.particleType)
    #             influence = influenceTable[particle.particleType.name][influenceIndex]
                
    #             if influence > 0 and dist < particle.minInfluenceDist:
    #                 impact = particle.minInfluenceDist - dist
    #                 impact *= 0.4
    #                 influence -= impact
                
    #             influence *= math.exp(-dist / maxInfluenceDist)
                
    #             if dist != 0:
    #                 dirX = dx / dist
    #                 dirY = dy / dist
                    
    #                 finalVelX += influence * dirX
    #                 finalVelY += influence * dirY
            
    #         particle.destX = particle.x + finalVelX
    #         particle.destY = particle.y + finalVelY





 # @staticmethod
    # def batchQuery():
    #     supercell_size = Particle.MAX_INFLUENCE_DIST
    #     supercell_map = collections.defaultdict(list)
    #     results = {p: [] for p in Constants.PARTICLES}
    #     results_lock = Lock()  # Lock for thread-safe access to results

    #     for p in Constants.PARTICLES:
    #         supercell_x = int(p.pos[0] // supercell_size)
    #         supercell_y = int(p.pos[1] // supercell_size)
    #         supercell_map[(supercell_x, supercell_y)].append(p)
    #         # results[p] = []


    #     def processSupercell(scx_scy_particles):
    #         scx, scy, particles_in_supercell = scx_scy_particles
    #         range_query = pygame.Rect(
    #             scx * supercell_size - Particle.MAX_INFLUENCE_DIST,
    #             scy * supercell_size - Particle.MAX_INFLUENCE_DIST,
    #             supercell_size + Particle.MAX_INFLUENCE_DIST * 2,
    #             supercell_size + Particle.MAX_INFLUENCE_DIST * 2
    #         )
    #         found = Constants.QUADTREE.query(range_query, [])

    #         local_results = collections.defaultdict(list)

    #         for p in particles_in_supercell:
    #             for f in found:
    #                 if f != p:
    #                     dist = -1
    #                     if local_results[f]:
    #                         for particle, recordedDist in local_results[f]:
    #                             if particle == p:
    #                                 dist = recordedDist
    #                                 break
                            

    #                     # Distance not previously calculated
    #                     if dist == -1:
    #                         dist = np.linalg.norm(p.pos - f.pos)
    #                         # print("not already calculated")
    #                     local_results[p].append((f, dist))# = [f for f in found if f != p]
            
    #         with results_lock:
    #             for p, neighbors in local_results.items():
    #                 results[p].extend(neighbors)

    #     supercells = [(scx, scy, particles) for (scx, scy), particles in supercell_map.items()]
        
    #     with ThreadPoolExecutor() as executor:
    #         executor.map(processSupercell, supercells)
    #     return results
    





# class Quadtree:
#     def __init__(self, x, y, width, height, max_particles=3, depth=0, max_depth=15):
#         self.bounds = pygame.Rect(x, y, width, height)
#         self.max_particles = max_particles
#         self.particles = []
#         self.divided = False
#         self.depth = depth
#         self.max_depth = max_depth

#     def subdivide(self):
#         x, y, w, h = self.bounds
#         hw, hh = int(w // 2), int(h // 2)

#         self.nw = Quadtree(x, y, hw, hh, self.max_particles, self.depth + 1, self.max_depth)
#         self.ne = Quadtree(x + hw, y, hw, hh, self.max_particles, self.depth + 1, self.max_depth)
#         self.sw = Quadtree(x, y + hh, hw, hh, self.max_particles, self.depth + 1, self.max_depth)
#         self.se = Quadtree(x + hw, y + hh, hw, hh, self.max_particles, self.depth + 1, self.max_depth)

#         self.divided = True

#     def insert(self, particle):
#         if not self.bounds.collidepoint(particle.x, particle.y):
#             return False

#         if len(self.particles) < self.max_particles or self.depth >= self.max_depth:
#             self.particles.append(particle)
#             # if self.depth >= self.max_depth:
#             #     print(self.depth)
#             return True
#         else:
#             if not self.divided:
#                 self.subdivide()

#             if self.nw.insert(particle) or self.ne.insert(particle) or self.sw.insert(particle) or self.se.insert(particle):
#                 return True

#     def clear(self):
#         self.particles = []
#         self.divided = False
#         self.northwest = None
#         self.northeast = None
#         self.southwest = None
#         self.southeast = None
        
#     def query(self, range, found):
#         if not self.bounds.colliderect(range):
#             return found

#         for p in self.particles:
#             if range.collidepoint(p.x, p.y):
#                 found.append(p)

#         if self.divided:
#             self.nw.query(range, found)
#             self.ne.query(range, found)
#             self.sw.query(range, found)
#             self.se.query(range, found)

#         return found
    
#     def update(self, particle):
#         # If the particle is still within the current quadtree bounds, do nothing
#         if self.bounds.collidepoint(particle.x, particle.y):
#             return

#         # Otherwise, remove the particle from this quadtree
#         if particle in self.particles:
#             self.particles.remove(particle)

#         # Try to insert the particle in one of the subdivided quadrants
#         if self.divided:
#             if self.nw.insert(particle) or self.ne.insert(particle) or self.sw.insert(particle) or self.se.insert(particle):
#                 return
#         else:
#             # If the particle cannot be inserted into a child, insert it into this quadtree
#             self.insert(particle)
    
    