import pygame

class Quadtree:
    def __init__(self, x, y, width, height, max_particles=3, depth=0, max_depth=15):
        self.bounds = pygame.Rect(x, y, width, height)
        self.max_particles = max_particles
        self.particles = []
        self.divided = False
        self.depth = depth
        self.max_depth = max_depth
        self.nw = self.ne = self.sw = self.se = None  # Initialize children to None

    def subdivide(self):
        x, y, w, h = self.bounds
        hw, hh = int(w // 2), int(h // 2)

        self.nw = Quadtree(x, y, hw, hh, self.max_particles, self.depth + 1, self.max_depth)
        self.ne = Quadtree(x + hw, y, hw, hh, self.max_particles, self.depth + 1, self.max_depth)
        self.sw = Quadtree(x, y + hh, hw, hh, self.max_particles, self.depth + 1, self.max_depth)
        self.se = Quadtree(x + hw, y + hh, hw, hh, self.max_particles, self.depth + 1, self.max_depth)

        self.divided = True

    def insert(self, particle):
        if not self.bounds.collidepoint(particle.pos[0], particle.pos[1]):
            return False

        if len(self.particles) < self.max_particles or self.depth >= self.max_depth:
            self.particles.append(particle)
            return True
        else:
            if not self.divided:
                self.subdivide()

            if self.nw.insert(particle) or self.ne.insert(particle) or self.sw.insert(particle) or self.se.insert(particle):
                return True


    def batchInsert(self, particles):
        if not self.divided:
            if len(particles) <= self.max_particles or self.depth >= self.max_depth:
                self.particles.extend(particles)
                return
            else:
                self.subdivide()

        nw_particles = []
        ne_particles = []
        sw_particles = []
        se_particles = []

        for particle in particles:
            if self.nw.bounds.collidepoint(particle.pos[0], particle.pos[1]):
                nw_particles.append(particle)
            elif self.ne.bounds.collidepoint(particle.pos[0], particle.pos[1]):
                ne_particles.append(particle)
            elif self.sw.bounds.collidepoint(particle.pos[0], particle.pos[1]):
                sw_particles.append(particle)
            elif self.se.bounds.collidepoint(particle.pos[0], particle.pos[1]):
                se_particles.append(particle)
            else:
                self.particles.append(particle)

        self.nw.batchInsert(nw_particles)
        self.ne.batchInsert(ne_particles)
        self.sw.batchInsert(sw_particles)
        self.se.batchInsert(se_particles)
            
            
    def clear(self):
        self.particles = []
        self.divided = False
        self.nw = self.ne = self.sw = self.se = None  # Clear children
        
    def query(self, range, found):
        if not self.bounds.colliderect(range):
            return found

        for p in self.particles:
            if range.collidepoint(p.pos[0], p.pos[1]):
                found.append(p)

        if self.divided:
            self.nw.query(range, found)
            self.ne.query(range, found)
            self.sw.query(range, found)
            self.se.query(range, found)

        return found
    
    
    
    def update(self, particle):
        # Check if the particle is still within the same quadtree
        if self.bounds.collidepoint(particle.pos[0], particle.pos[1]):
            return  # No need to update if the particle is still within the same quadtree

        # Remove the particle from this quadtree if it exists
        if particle in self.particles:
            self.particles.remove(particle)
            
        # Reinsert the particle in the correct quadtree
        self.insert(particle)
        

    def batchUpdate(self, particles):
        # Clear the quadtree before re-inserting particles
        self.clear()
        self.batchInsert(particles)
        
        
        
        