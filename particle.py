import random
import pygame
import numpy as np
import math
import collections
from enum import Enum
from constants import Constants
from concurrent.futures import ThreadPoolExecutor
from threading import Lock



class Particle():
    __particleAttractions = None
    MAX_INFLUENCE_DIST = 120
    MAX_INFLUENCE_DIST_SQUARED = MAX_INFLUENCE_DIST ** 2
    MIN_INFLUENCE_DIST = 5

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
        if Particle.__particleAttractions is None:
            Particle.__particleAttractions = {}
            
            # Initialize to list of 0's
            for p in Particle.particleTypes:
                Particle.__particleAttractions[p.name] = [0] * len(Particle.particleTypes)
            
            typesList = list(Particle.particleTypes)
            for i, p in enumerate(typesList):
                for j in range (i, len(Particle.particleTypes)):
                    if i == j:
                        # Diagonals should be the same (similar particles should act the same)
                        Particle.__particleAttractions[p.name][j] = random.uniform(-0.4, 0.4)
                    else:
                        value = random.uniform(-0.4, 0.4)
                        Particle.__particleAttractions[p.name][j] = random.uniform(-0.4, 0.4)
                        Particle.__particleAttractions[list(Particle.particleTypes)[j].name][i] = random.uniform(-0.4, 0.4)
                        
        return Particle.__particleAttractions


    def update(self):
        self.calcVelocity()
        self.move()
        self.draw()
        # Constants.QUADTREE.update(self)
        
        

    
    @staticmethod
    def batchQuery():
        supercell_size = Particle.MAX_INFLUENCE_DIST
        supercell_map = collections.defaultdict(list)
        results = {p: [] for p in Constants.PARTICLES}
        results_lock = Lock()  # Lock for thread-safe access to results

        for p in Constants.PARTICLES:
            supercell_x = int(p.pos[0] // supercell_size)
            supercell_y = int(p.pos[1] // supercell_size)
            supercell_map[(supercell_x, supercell_y)].append(p)
            # results[p] = []


        def processSupercell(scx_scy_particles):
            scx, scy, particles_in_supercell = scx_scy_particles
            range_query = pygame.Rect(
                scx * supercell_size - Particle.MAX_INFLUENCE_DIST,
                scy * supercell_size - Particle.MAX_INFLUENCE_DIST,
                supercell_size + Particle.MAX_INFLUENCE_DIST * 2,
                supercell_size + Particle.MAX_INFLUENCE_DIST * 2
            )
            found = Constants.QUADTREE.query(range_query, [])

            local_results = collections.defaultdict(list)

            for p in particles_in_supercell:
                for f in found:
                    if f != p:
                        dist = -1
                        if local_results[f]:
                            for particle, recordedDist in local_results[f]:
                                if particle == p:
                                    dist = recordedDist
                                    break
                            

                        # Distance not previously calculated
                        if dist == -1:
                            dist = np.linalg.norm(p.pos - f.pos)
                            # print("not already calculated")
                        local_results[p].append((f, dist))# = [f for f in found if f != p]
            
            with results_lock:
                for p, neighbors in local_results.items():
                    results[p].extend(neighbors)

        supercells = [(scx, scy, particles) for (scx, scy), particles in supercell_map.items()]
        
        with ThreadPoolExecutor() as executor:
            executor.map(processSupercell, supercells)
        return results
    
    def calcVelocity(self):

        influenceTable = Particle.getParticleAttractions()
        
        finalVelX, finalVelY = 0, 0
            
        neighbors = Constants.PARTICLE_NEIGHBORS[self]
        for p in neighbors:
            
            if p[1] != -1:
                dist = p[1]
            else:
                print("maybe shouldnt need this")
                dist = np.linalg.norm(p[0].pos - self.pos)
                
            if dist > Particle.MAX_INFLUENCE_DIST:
                continue
                
                
            influenceIndex = self.particleTypeByEnum(p[0].particleType)
            influence = influenceTable[p[0].particleType.name][influenceIndex]
                
            if influence > 0 and dist < Particle.MIN_INFLUENCE_DIST:
                impact = Particle.MIN_INFLUENCE_DIST - dist
                impact *= 0.4
                influence -= impact
                
            influence *= math.exp(-dist / Particle.MAX_INFLUENCE_DIST)
                
            if dist != 0:
                dirX = (self.pos[0] - p[0].pos[0]) / dist
                dirY = (self.pos[1] - p[0].pos[1]) / dist
                    
                finalVelX += influence * dirX
                finalVelY += influence * dirY
        
        self.vel[0] = finalVelX
        self.vel[1] = finalVelY


    def move(self):
        self.pos = self.pos + self.vel






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

    
    def draw(self):
        pygame.draw.circle(Constants.SCREEN, self.particleType.value, (self.pos[0], self.pos[1]), self.size)

    
    def particleTypeByIndex(self, index):
        switch = {
            0: self.particleTypes.PINK,
            1: self.particleTypes.TEAL,
            2: self.particleTypes.GREY,
            3: self.particleTypes.MAIZE,
            4: self.particleTypes.INDIGO,
            5: self.particleTypes.ORANGE
        }
        return switch.get(index)

    def particleTypeByEnum(self, enum):
        switch = {
            self.particleTypes.PINK: 0,
            self.particleTypes.TEAL: 1,
            self.particleTypes.GREY: 2,
            self.particleTypes.MAIZE: 3,
            self.particleTypes.INDIGO: 4,
            self.particleTypes.ORANGE: 5,
        }
        return switch.get(enum)

    class particleTypes(Enum):
        PINK = (255, 130, 169)
        TEAL = (44, 175, 201)
        GREY = (156, 174, 169)
        MAIZE = (244, 224, 77)
        INDIGO = (84, 13, 110)
        ORANGE = (224, 92, 21)





















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
    
    