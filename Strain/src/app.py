from engine import Engine
from graphicsengine import GraphicsEngine
        
class App():
    def __init__(self):
        self.engine = Engine() 
        self.engine.start()
        
        self.graphics = GraphicsEngine()
        self.graphics.run()
