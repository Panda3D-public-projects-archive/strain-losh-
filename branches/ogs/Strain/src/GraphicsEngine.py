from panda3d.core import NodePath, Point2, Point3, CardMaker, VBase4, Vec3, GeomNode
from panda3d.core import ShadeModelAttrib, DirectionalLight, AmbientLight, TransparencyAttrib
from direct.interval.IntervalGlobal import Sequence, ActorInterval, Parallel, SoundInterval
from direct.gui.DirectGui import DirectFrame, DirectLabel, DGG
from ResourceManager import UnitLoader
from direct.showbase import DirectObject

#===============================================================================
# CLASS UnitModel --- DEFINITION
#===============================================================================

class UnitModel:
    def __init__(self, model, unit, player):
        self.model = model
        self.id = str(unit.id)
        self.model.setPos(self.get_unit_model_pos(unit.pos))
        self.model.setLightOff()
        self.model.setTag("type", "unit")
        self.model.setTag("id", self.id)
        self.model.setTag("player", str(player.id))
        self.model.setTag("team", player.team)

        self.node = NodePath(self.id)
        self.dummy_node = NodePath("dummy_"+self.id)
        self.dest_node = NodePath("dest_"+self.id)
        if player.team == "1":
            self.team_color = VBase4(1, 0, 0, 0)
        elif player.team == "2":
            self.team_color = VBase4(0, 0, 1, 0)

        self.model.reparentTo(self.node)
        self.dummy_node.reparentTo(self.node)
        self.dest_node.reparentTo(self.node)
        
    def get_unit_model_pos(self, pos):
        return Point3(pos.x + 0.5, pos.y + 0.5, 0.3)
    
    def get_unit_grid_pos(self):
        pos = self.model.getPos()
        return Point2(int(pos.x), int(pos.y))
    
    def create_move_animation(self, tile_list, dest):
        intervals = []
        movement = []
        seq = Sequence()
        dur = 0
        end = None
        for n in tile_list:
            if n[0] == dest:
                end = n
                break
        while end:
            endpos = base.calc_unit_pos(Point3(end[0].x, end[0].y, 0))
            parent = end[1]
            if parent is None:
                break
            else:
                startpos = base.calc_unit_pos(Point3(parent[0].x, parent[0].y, 0))
                tupple = (startpos, endpos)
                movement.append(tupple)             
            end = end[1]
        movement.reverse()
        h = self.model.getH()
        for m in movement:
            self.dummy_node.setPos(m[0].x, m[0].y, 0)
            self.dest_node.setPos(m[1].x, m[1].y, 0)
            self.dummy_node.lookAt(self.dest_node)
            endh = self.dummy_node.getH()
            if endh != h:
                i = self.model.quatInterval(0.2, hpr = Vec3(endh, 0, 0), startHpr = Vec3(h, 0, 0))
                intervals.append(i)
                h = endh
                dur = dur + 0.2
            i = self.model.posInterval(0.5, m[1], m[0])
            dur = dur + 0.5
            intervals.append(i)
        for i in intervals:
            seq.append(i)
        anim = ActorInterval(self.model, 'run', loop = 1, duration = dur)
        s = SoundInterval(self.get_sound('movend'))
        move = Sequence(Parallel(anim, seq), s)
        move.start()
        
class Gui(DirectObject.DirectObject):
    def __init__(self):
        wp = base.win.getProperties() 
        aspect = float(wp.getXSize()) / wp.getYSize()
        self.sel_frame = DirectLabel(frameColor=(1,1,1,1) , frameSize=(0,0.3,0,0.3 ), pos = (-aspect, 0, 0.7))
        self.sel_frame.reparentTo(aspect2d)
        self.sel_frame.setTransparency(1)
        plane = loader.loadModel('plane')
        plane.setScale(2)
        plane.flattenLight()
        f = GuiFrame(0.3, 0.3, 0.01, Vec3(-aspect, 0, 0.7), VBase4(0, 0, 0, 0))
        self.deselect_button = GuiButton(Point3(-aspect + 0.3 + 0.05, 0, 0.95), plane, aspect, "deselect")
        self.punit_button = GuiButton(Point3(-aspect + 0.4 + 0.05, 0, 0.95), plane, aspect, "prev_unit")
        self.nunit_button = GuiButton(Point3(-aspect + 0.5 + 0.05, 0, 0.95), plane, aspect, "next_unit")
        
        self.hovered_gui = None
        
        self.accept('mouse1-up', self.process_mouseclick)
        
        taskMgr.add(self.process_gui, 'process_gui_task')
    
    def process_mouseclick(self):
        if self.hovered_gui == self.deselect_button:
            base.interface.deselectUnit()
        elif self.hovered_gui == self.punit_button:
            base.interface.select_prev_unit()
        elif self.hovered_gui == self.nunit_button:
            base.interface.select_next_unit()            
    
    def process_gui(self, task):
        if base.mouseWatcherNode.hasMouse(): 
            mpos = base.mouseWatcherNode.getMouse()
            if mpos.x >= self.deselect_button.pos_min_x and mpos.x <= self.deselect_button.pos_max_x and mpos.y >= self.deselect_button.pos_min_y and mpos.y <= self.deselect_button.pos_max_y:
                self.hovered_gui = self.deselect_button
                self.deselect_button.frame.setAlphaScale(1)                
                self.punit_button.frame.setAlphaScale(0.5)
                self.nunit_button.frame.setAlphaScale(0.5)
            elif mpos.x >= self.punit_button.pos_min_x and mpos.x <= self.punit_button.pos_max_x and mpos.y >= self.punit_button.pos_min_y and mpos.y <= self.punit_button.pos_max_y:
                self.hovered_gui = self.punit_button
                self.deselect_button.frame.setAlphaScale(0.5)                
                self.punit_button.frame.setAlphaScale(1)
                self.nunit_button.frame.setAlphaScale(0.5)
            elif mpos.x >= self.nunit_button.pos_min_x and mpos.x <= self.nunit_button.pos_max_x and mpos.y >= self.nunit_button.pos_min_y and mpos.y <= self.nunit_button.pos_max_y:
                self.hovered_gui = self.nunit_button
                self.deselect_button.frame.setAlphaScale(0.5)                
                self.punit_button.frame.setAlphaScale(0.5)
                self.nunit_button.frame.setAlphaScale(1)                
            else:
                self.hovered_gui = None
                self.deselect_button.frame.setAlphaScale(0.5)                
                self.punit_button.frame.setAlphaScale(0.5)
                self.nunit_button.frame.setAlphaScale(0.5)
        return task.cont

class GuiFrame:
    def __init__(self, width, height, border_size, pos, color):
        self.node = NodePath("frame")
        cm = CardMaker("cm_left")
        cm.setFrame(0, border_size, 0, height)
        n = self.node.attachNewNode(cm.generate())
        n.setPos(0, 0, 0)
        cm = CardMaker("cm_right")
        cm.setFrame(0, border_size, 0, height)
        n = self.node.attachNewNode(cm.generate())
        n.setPos(width - border_size, 0, 0)
        cm = CardMaker("cm_top")
        cm.setFrame(0, width, height - border_size, width)
        n = self.node.attachNewNode(cm.generate())
        n.setPos(0, 0, 0)
        cm = CardMaker("cm_bottom")
        cm.setFrame(0, width, 0, border_size)
        n = self.node.attachNewNode(cm.generate())
        n.setPos(0, 0, 0)
        self.node.reparentTo(aspect2d)
        self.node.setColor(color)
        self.node.setPos(pos)
        self.node.flattenStrong()

class GuiButton:
    def __init__(self, pos, plane, aspect, name):
        self.node = aspect2d.attachNewNode("guibutton")
        self.node.setTransparency(TransparencyAttrib.MAlpha)
        self.node.setAlphaScale(0.5) 
        geom = GeomNode('plane')
        geom.addGeomsFrom(plane.getChild(0).getChild(0).node())
        self.frame = self.node.attachNewNode(geom) 
        self.frame.setScale(0.05)
        self.frame.setPos(pos)
        self.node.setTexture(loader.loadTexture(name+".png"))
        posx, posy = self.frame.getTightBounds()
        self.pos_min_x = posx.getX() / aspect
        self.pos_min_y = posx.getZ()
        self.pos_max_x = posy.getX() / aspect
        self.pos_max_y = posy.getZ()

class GraphicsEngine:
    
    unit_models = {}
    
    def __init__(self, engine):
        self.engine = engine
        self.node = render.attachNewNode("master")

        self.init_level(engine.level)
        self.load_unit_models()
        self.color_unit_tiles()
        self.init_lights()
        self.gui = Gui()
        self.init_alt_render()
        
    def init_alt_render(self):
        alt_buffer = base.win.makeTextureBuffer("texbuf", 256, 256)
        self.alt_render = NodePath("offrender")
        self.alt_cam = base.makeCamera(alt_buffer)
        self.alt_cam.reparentTo(self.alt_render)        
        self.alt_cam.setPos(0,-10,0)
        self.alt_render.setLightOff()
        self.alt_render.setFogOff()
        self.gui.sel_frame["frameTexture"] = alt_buffer.getTexture()
               
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
                #c.flattenLight()
                c.reparentTo(self.level_node)
            self.node_data.append(tile_nodes)
    
    def load_unit_models(self):
        ul = UnitLoader()
        for player in self.engine.players:
            for u in player.unitlist:
                model = ul.load(u.type, "render")
                um = UnitModel(model, u, player)
                um.node.reparentTo(self.node)
                self.unit_models[u.id] = um
                self.unit_data[u.x][u.y] = um

    def color_unit_tiles(self):
        for unit in self.unit_models.itervalues():
            u = base.engine.units[int(unit.id)]
            tile = self.node_data[int(u.x)][int(u.y)]
            base.interface.changeTileColor(tile, "_tile_unit_pos", unit.team_color)
