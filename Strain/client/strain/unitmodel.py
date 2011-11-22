from direct.actor.Actor import Actor
from panda3d.core import Vec4, Point4, Point3, Point2, NodePath#@UnresolvedImport
from panda3d.core import PointLight#@UnresolvedImport
from panda3d.core import TransparencyAttrib, TextureStage#@UnresolvedImport
from direct.interval.IntervalGlobal import Sequence, ActorInterval, Parallel, Func
import random
import utils

#===============================================================================
# CLASS UnitModel --- DEFINITION
#===============================================================================
class UnitModel:
    def __init__(self, parent, unit_id, off=False):
        self.parent = parent
        self.id = str(unit_id)

        self.node = NodePath("unit_"+self.id)
        self.dummy_node = NodePath("dummy_unit_"+self.id)
        self.dest_node = NodePath("dest_unit_"+self.id)
        
        # Get unit data from the Client
        unit = self.parent.parent.getUnitData(unit_id)
        if unit['owner_id'] == "1":
            self.team_color = Vec4(0.7, 0.2, 0.3, 1)
        elif unit['owner_id'] == "2":
            self.team_color = Vec4(0.106, 0.467, 0.878, 1)
        else:
            self.team_color = Vec4(0, 1, 0, 1)        
        self.model = self.load(unit['name'])
        
        self.model.reparentTo(self.node)
        self.dummy_node.reparentTo(self.node)
        self.dest_node.reparentTo(self.node)        
        
        if not off:
            scale = 0.25
            h = 180
            pos = Point3(int(unit['pos'][0]), int(unit['pos'][1]), 0)
            pos = self.calcWorldPos(pos)
        else:
            scale = 1
            h = 0
            pos = Point3(0, 1.7, -2.1)
        
        # Bake in rotation transform because model is created facing towards screen (h=180)
        self.model.setScale(scale)
        self.model.setH(h)
        self.model.flattenLight() 
        self.node.setPos(pos)

        #self.model.setLightOff()
        self.node.setTag("type", "unit")
        self.node.setTag("id", str(self.id))        
        self.node.setTag("player_id", str(unit['owner_id']))
        self.node.setTag("team", str(unit['owner_id']))

        # If unit model is not rendered for portrait, set its heading as received from server
        if not off:
            self.setHeading(unit)
            
        self.marker = Actor("ripple2") 
        self.marker.reparentTo(self.node)
        self.marker.setP(-90)
        self.marker.setScale(0.7, 0.7, 0.7)
        self.marker.setColor(self.team_color)
        
        
        plight = PointLight('plight')
        plight.setColor(Point4(0.2, 0.2, 0.2, 1))
        plnp = self.node.attachNewNode(plight)
        plnp.setPos(0, 0, 0)
        
        self.marker.setLight(plnp)
        self.marker.setTransparency(TransparencyAttrib.MAlpha)
        self.marker.setAlphaScale(0.5) 
        self.marker.setTag("type", "unit_marker")
        
        self.marker.setPos(0, 0, 0.02)
        #self.marker.flattenLight()
        #self.marker.hide()
        
        self.passtime = 0
        self.setIdleTime()
    
    def load(self, unit_type):
        if unit_type == 'marine_common' or unit_type == 'marine_epic':
            model = Actor('marine') 
            model.node_dict = {}
            for gear in utils.gear_list:
                for item in gear.itervalues():
                    for node in item:
                        if isinstance(node, tuple):
                            n = node[0]
                            n_tex = node[1]
                        else:
                            n = node
                            n_tex = node
                        model.node_dict[n] = model.find("**/"+n)
                        model.node_dict[n].setTag("node", n)
                        if n not in utils.unit_types[unit_type]:
                            model.node_dict[n].detachNode()
                            #model.node_dict[n].remove()
                        else:
                            if n_tex:
                                tex_dif = loader.loadTexture(n_tex+"_dif.tga")
                                model.node_dict[n].setTexture(tex_dif)
                                """
                                ts_spc = TextureStage('ts_spc')
                                tex_spc = loader.loadTexture(n_tex+"_spc.tga")
                                ts_spc.setMode(TextureStage.MGloss)
                                model.node_dict[n].setTexture(ts_spc, tex_spc)
                                ts_nrm = TextureStage('ts_nrm')
                                tex_nrm = loader.loadTexture(n_tex+"_nrm.tga")
                                ts_nrm.setMode(TextureStage.MNormal)
                                model.node_dict[n].setTexture(ts_nrm, tex_nrm)
                                if n == "power_armour_common" or n=="power_armour_gabriel":
                                    ts_tem = TextureStage('ts_tem')
                                    tex_tem = loader.loadTexture(n_tex+"_tem.dds")
                                    ts_tem.setMode(TextureStage.MBlend)
                                    ts_tem.setColor(self.team_color)
                                    model.node_dict[n].setTexture(ts_tem, tex_tem)
                                """
            model.loadAnims(utils.anim_dict)
            return model
    
    def moveUnitModel(self, action_list):
        intervals = []
        duration = 0.0
        start_pos = self.node.getPos()
        end_pos = None
        for idx, action in enumerate(action_list):
            type = action[0]
            if idx == 0:
                curr_pos = start_pos
                curr_h = self.model.getH()
            else:
                curr_pos = dest_pos
                curr_h = dest_h
                
            if type == "move":
                dest_pos = Point3(action[1][0] + 0.5, action[1][1] + 0.5, 0.3)
                self.dummy_node.setPos(render, curr_pos)
                self.dest_node.setPos(render, dest_pos)
                self.dummy_node.lookAt(self.dest_node)
                dest_h = self.dummy_node.getH()
                # Model heading is different than movement heading, first create animation that turns model to his destination
                i_h = None
                if dest_h != curr_h:
                    i_h = self.model.quatInterval(0.2, hpr = Point3(dest_h, 0, 0), startHpr = Point3(curr_h, 0, 0))
                    curr_h = dest_h
                i = self.node.posInterval(0.5, dest_pos, curr_pos)
                duration = duration + 0.5
                if i_h:
                    p = Parallel(i, i_h)
                else:
                    p = i
                intervals.append(p)
                end_pos = dest_pos
            elif type == "rotate":
                dest_pos = Point3(action[1][0] + 0.5, action[1][1] + 0.5, 0.3)
                self.dummy_node.setPos(render, curr_pos)
                self.dest_node.setPos(render, dest_pos)
                self.dummy_node.lookAt(self.dest_node)
                dest_h = self.dummy_node.getH() 
                i_h = self.model.quatInterval(0.2, hpr = Point3(dest_h, 0, 0), startHpr = Point3(curr_h, 0, 0))
                duration = duration + 0.2
                intervals.append(i_h)                 
        seq = Sequence()
        for i in intervals:
            seq.append(i)
        #return
        anim = ActorInterval(self.model, 'run', loop = 1, duration = duration)
        anim_end = ActorInterval(self.model, 'idle_stand01', startFrame=1, endFrame=1)
        move = Sequence(Func(self.parent.parent.beforeUnitAnimHook, int(self.id)),
                        Parallel(anim, seq),
                        Sequence(anim_end),
                        Func(self.parent.parent.afterUnitAnimHook, int(self.id), start_pos, end_pos)
                        )
        move.start()

    
    def setIdleTime(self):
        self.idletime = random.randint(10, 20)
    
    def reparentTo(self, node):
        self.node.reparentTo(node)
    
    def getAnimName(self, anim_type):
        num = random.randint(1, self.anim_count_dict[anim_type])
        return anim_type + str(num).zfill(2)    
    
    def calcWorldPos(self, pos):
        return pos + Point3(0.5, 0.5, 0.3)  
        
    def getHeadingTile(self, unit):
        x = int(unit['pos'][0])
        y = int(unit['pos'][1])  
        heading = unit['heading']  
        
        if heading == utils.HEADING_NW:
            o = Point2(x-1, y+1)
        elif heading == utils.HEADING_N:
            o = Point2(x, y+1)
        elif heading == utils.HEADING_NE:
            o = Point2(x+1, y+1)
        elif heading == utils.HEADING_W:
            o = Point2(x-1, y)
        elif heading == utils.HEADING_E:
            o = Point2(x+1, y)
        elif heading == utils.HEADING_SW:
            o = Point2(x-1, y-1)
        elif heading == utils.HEADING_S:
            o = Point2(x, y-1)
        elif heading == utils.HEADING_SE:
            o = Point2(x+1, y-1)
        return o
    
    def setHeading(self, heading):
        tile_pos = self.getHeadingTile(heading)
        self.dest_node.setPos(render, tile_pos.getX()+0.5, tile_pos.getY()+0.5, 0.3)
        self.model.lookAt(self.dest_node)
        
        
    def cleanup(self):
        self.model.cleanup()
        
    def remove(self):
        self.model.remove()
    
