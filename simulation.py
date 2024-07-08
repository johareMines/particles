from constants import Constants
import pygame
import time
import sys
from particle import Particle
from quadtree import Quadtree
import psutil
import threading
from concurrent.futures import ThreadPoolExecutor

class Simulation:
    __instance = None
    def __init__(self, width=1920, height=1080):
        if Simulation.__instance is not None:
            raise Exception("Singleton can't be instantiated multiple times.")
        else:
            pygame.init()

            # Windowed
            # self.screen = pygame.display.set_mode((width, height))
            
            screenInfo = pygame.display.Info()

            Constants.SCREEN_WIDTH = screenInfo.current_w
            Constants.SCREEN_HEIGHT = screenInfo.current_h

            Constants.SCREEN = pygame.display.set_mode((Constants.SCREEN_WIDTH, Constants.SCREEN_HEIGHT), pygame.FULLSCREEN | pygame.RESIZABLE, display=Constants.DISPLAY.value)
            
            self.clock = pygame.time.Clock()
            self.frame_times = []
            self.frame_print_time = time.time()

            self.performanceMonitor = PerformanceMonitor(Constants.MONITOR_INTERVAL) # Interval in seconds
            self.performanceMonitor.start()
                
    @staticmethod
    def get_instance():
        # Static method to get the singleton instance
        if Simulation.__instance is None:
            Simulation.__instance = Simulation()
        return Simulation.__instance

    def run(self):
        running = True
        
        Constants.QUADTREE = Quadtree(0, 0, Constants.SCREEN_WIDTH, Constants.SCREEN_HEIGHT)
        # Insert particles into the quadtree
        for particle in Constants.PARTICLES:
            Constants.QUADTREE.insert(particle)
        
        # Start velocity updating thread
        velThread = threading.Thread(target=Particle.updateVelocities)
        velThread.start()
        
        while running:
            start_time = time.time() # For framerate calculation
            for event in pygame.event.get():
                if event.type == pygame.QUIT:
                    running = False
                elif event.type == pygame.KEYDOWN:
                    if event.key == pygame.K_ESCAPE:
                        running = False
            
            Constants.SCREEN.fill((0, 0, 0))  # Clear the screen
            
            # # Clear quadtree (more efficient than making a new one)
            # Constants.QUADTREE.clear()

            # Particle.batchCalcDest(Constants.PARTICLES)
            # Constants.PARTICLE_NEIGHBORS = Particle.batchQuery()
            
            for particle in Constants.PARTICLES:
                particle.update()
            
            # with ThreadPoolExecutor() as executor:
            #     executor.map(lambda particle: particle.update(), Constants.PARTICLES)
            
            for particle in Constants.PARTICLES:
                Constants.QUADTREE.update(particle)
            
                
            # Draw circle at mouse position
            # self.drawMouseCircle()
            
            pygame.display.flip() # Update display
            
            # Calc framerate
            self.clock.tick(60)  # FPS Limit
            end_time = time.time() 
            frame_time = end_time - start_time
            self.frame_times.append(frame_time)
            if len(self.frame_times) > 200:
                self.frame_times.pop(0)
            self.calculateFramerate()
            
            
            
        self.performanceMonitor.stop()
        self.performanceMonitor.join()
        
        velThread.join()
        pygame.quit()
        sys.exit()
        
    def drawMouseCircle(self):
        mouse_x, mouse_y = pygame.mouse.get_pos()
        if 0 <= mouse_x <= Constants.SCREEN_WIDTH and 0 <= mouse_y <= Constants.SCREEN_HEIGHT:
            pygame.draw.circle(Constants.SCREEN, (0, 255, 0), (mouse_x, mouse_y), 10)
            print("Mouse x: {} | Mouse y: {}".format(mouse_x, mouse_y))
    
    def calculateFramerate(self):
        if time.time() - self.frame_print_time < Constants.MONITOR_INTERVAL:
            return
        
        if len(self.frame_times) < 200:
            return
            
        avg_frame_time = sum(self.frame_times) / len(self.frame_times)
        fps = 1.0 / avg_frame_time
        print(f"FPS: {round(fps, 1)}")

        self.frame_print_time = time.time()
            
    
    
class PerformanceMonitor(threading.Thread):
    def __init__(self, interval):
        super().__init__()
        self.interval = interval
        self.stopped = threading.Event()
        self.process = psutil.Process()

    def run(self):
        while not self.stopped.wait(self.interval):
            self.monitorCPU()
            self.monitorMemory()
            self.monitorObjects()

    def monitorCPU(self):
        cpu_percent = self.process.cpu_percent()
        print(f"CPU usage: {cpu_percent}%")
    
    def monitorMemory(self):
        memory_info = self.process.memory_info()
        print(f"Memory Usage: {memory_info.rss / (1024 * 1024)} MB")  # Convert to MB
    
    def monitorObjects(self):
        print(f"Particles: {len(Constants.PARTICLES)}")
    
    def stop(self):
        self.stopped.set()
