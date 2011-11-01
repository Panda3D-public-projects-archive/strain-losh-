from engine.engineCore import Engine
from graphicsengine import GraphicsEngine
import sys
        
class App():
    def __init__(self):
        
        if 'engine' in sys.argv:
            self.engine = Engine() 
            self.engine.start()
        
        if 'client' in sys.argv:
            self.graphics = GraphicsEngine()
            self.graphics.run()
