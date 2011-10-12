from Engine import Engine
from GraphicsEngine import GraphicsEngine
        
class App():
    def __init__(self):
        self.engine = Engine() 
        self.graphics = GraphicsEngine(self.engine)
        
        self.graphics.run()
