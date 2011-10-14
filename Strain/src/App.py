from Engine import Engine
from GraphicsEngine import GraphicsEngine
        
class App():
    def __init__(self):
        self.engine = Engine() 
        self.engine.start()
        self.graphics = GraphicsEngine()
        
        self.graphics.run()
