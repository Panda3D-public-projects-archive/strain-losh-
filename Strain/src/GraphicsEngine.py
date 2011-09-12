from panda3d.core import NodePath, Point2, Point3, CardMaker, VBase4
from panda3d.core import ShadeModelAttrib, DirectionalLight, AmbientLight
from ResourceManager import UnitLoader


class UnitModel:
    def __init__(self, model, unit):
        self.model = model
        self.id = str(unit.id)
        self.model.setPos(self.get_unit_model_pos(unit.pos))
        self.model.setLightOff()
        self.model.setTag("type", "unit")
        self.model.setTag("id", self.id)

        self.node = NodePath(self.id)
        self.dummy_node = NodePath("dummy_"+self.id)
        self.dest_node = NodePath("dest_"+self.id)

        self.model.reparentTo(self.node)
        self.dummy_node.reparentTo(self.node)
        self.dest_node.reparentTo(self.node)
        
    def get_unit_model_pos(self, pos):
        return Point3(pos.x + 0.5, pos.y + 0.5, 0.3)
    
    def get_unit_grid_pos(self):
        pos = self.model.getPos()
        return Point2(int(pos.x), int(pos.y))

class GraphicsEngine:
    
    unit_models = {}
    
    def __init__(self, engine):
        self.engine = engine
        self.node = render.attachNewNode("master")
        
        wp = base.win.getProperties() 
        aspect = float(wp.getXSize()) / wp.getYSize()        
        cm = CardMaker("unit")
        cm.setFrame(0, 0.3, 0, 0.3)
        self.unit_cm = aspect2d.attachNewNode(cm.generate())
        self.unit_cm.setPos(-aspect, 0, 0.7)
        self.init_alt_render()
        
        self.init_level(engine.level)
        self.load_unit_models()
        self.init_lights()
        
    def init_alt_render(self):
        alt_buffer = base.win.makeTextureBuffer("texbuf", 256, 256)
        self.alt_render = NodePath("offrender")
        self.alt_cam = base.makeCamera(alt_buffer)
        self.alt_cam.reparentTo(self.alt_render)        
        self.alt_cam.setPos(0,-10,0)
        self.alt_render.setLightOff()
        self.alt_render.setFogOff()     
        self.unit_cm.setTexture(alt_buffer.getTexture())
               
    def init_lights(self):
        shade = ShadeModelAttrib.make(ShadeModelAttrib.MSmooth)
        render.setAttrib(shade)
        dlight1 = DirectionalLight("dlight1")
        dlight1.setColor(VBase4(1.0, 1.0, 1.0, 1.0))
        dlnp1 = render.attachNewNode(dlight1)
        dlnp1.setHpr(-10, -30, 0)
        render.setLight(dlnp1)
        alight = AmbientLight("alight")
        alight.setColor(VBase4(0.3, 0.3, 0.3, 1.0))
        alnp = render.attachNewNode(alight)
        render.setLight(alnp)
    
    def init_level(self, level):
        self.level_node = render.attachNewNode("levelnode")
        self.node_data = []
        self.unit_data = [[None] * level.maxX for i in xrange(level.maxY)]
        for x in xrange(0, level.maxX): 
            tile_nodes = []
            for y in xrange(0, level.maxY): 
                tag = level._level_data[x][y]
                c = loader.loadModel("tile")
                c.setPos(x, y, 0)
                c.setTag("pos", "%(maxX)s-%(maxY)s" % {"maxX":x, "maxY":y})
                c.setTag("type", "tile")
                tile_nodes.append(c) 
                if tag != 0:
                    c.setScale(1, 1, tag + 1)
                    coef = 1 + 0.05*tag
                    c.setColorScale(coef, coef, coef, 1)
                c.reparentTo(self.level_node)
            self.node_data.append(tile_nodes)
    
    def load_unit_models(self):
        ul = UnitLoader()
        for player in self.engine.players:
            for u in player.unitlist:
                model = ul.load(u.type, "render")
                um = UnitModel(model, u)
                um.node.reparentTo(self.node)
                self.unit_models[u.id] = um
                self.unit_data[u.x][u.y] = um

