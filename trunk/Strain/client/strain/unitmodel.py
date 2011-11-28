from direct.actor.Actor import Actor
from panda3d.core import Vec4, Point4, Point3, Point2, NodePath, TextNode#@UnresolvedImport
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
        #self.dummy_node = NodePath("dummy_unit_"+self.id)
        #self.dest_node = NodePath("dest_unit_"+self.id)
        
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
        #self.dummy_node.reparentTo(self.node)
        #self.dest_node.reparentTo(self.node)        
        
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
        
        self.target_unit = None
    
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
                                tex_dif = loader.loadTexture(n_tex+"_dif.dds")
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
            utils.initAnims(model, unit_type)
            return model
   
    def shootUnit(self, weapon, damage_list):
        seq = Sequence()
        enemy_unit = self.target_unit
        # First we create our orientation animation (turning towards enemy unit)
        curr_h = self.model.getH(render)
        self.dummy_node.setPos(render, self.model.getPos(render))
        self.dest_node.setPos(render, enemy_unit.model.getPos(render))
        self.dummy_node.lookAt(self.dest_node)
        dest_h = self.dummy_node.getH(render)
        dest_h = utils.getHeadingAngle(utils.clampToHeading(dest_h))
        i_h = self.model.quatInterval(0.2, hpr = Point3(dest_h, 0, 0), startHpr = Point3(curr_h, 0, 0))
        seq.append(i_h)
        # Then we create shooting animation
        shoot_anim = ActorInterval(self.model, 'shoot')
        # Then we create the bullet and its animation
        self.bullet = loader.loadModel("sphere")
        self.bullet.setScale(0.05)
        start_pos = Point3(self.model.getX(render), self.model.getY(render), 0.9)
        end_pos = Point3(self.dest_node.getX(render), self.dest_node.getY(render), 0.9)
        time = round(self.model.getDistance(self.dest_node) / 5, 2)
        bullet_sequence = Sequence(Func(self.parent.setBullet, self.bullet),
                                   self.bullet.posInterval(time, end_pos, start_pos),
                                   Func(self.parent.deleteBullet, self.bullet)
                                   )
        # Pack unit shoot animation and bullet animation in parallel
        shoot_parallel = Parallel(shoot_anim, bullet_sequence)
        seq.append(shoot_parallel)
        # Find all damaged units and play their damage/kill/miss animation
        damage_parallel = Parallel()
        for action in damage_list:
            damage_type = action[0]
            target_unit_id = action[1]
            target_unit = self.parent.unit_np_dict[target_unit_id]
            t = TextNode('dmg')
            if damage_type == "bounce":
                target_anim = ActorInterval(target_unit.model, "damage")
                dmg = 'bounce'
            elif damage_type == "miss":
                target_anim = ActorInterval(target_unit.model, "damage")
                dmg = 'miss'                
            elif damage_type == "damage":
                target_anim = ActorInterval(target_unit.model, "damage")
                dmg = str(action[2])
            elif damage_type == "kill":
                target_anim = ActorInterval(target_unit.model, "die")
                dmg = str(action[2])
            t.setText( "%s" % dmg)
            t.setTextColor(1, 0, 0, 1)
            t.setAlign(TextNode.ACenter)
            textNodePath = NodePath("textnp")
            textNodePath.attachNewNode(t)
            textNodePath.setScale(0.25)
            textNodePath.setBillboardPointEye()
            start_pos = Point3(self.dest_node.getX(render), self.dest_node.getY(render), 0.9)
            end_pos = start_pos + Point3(0, 0, 3)
            damage_text_sequence = Sequence(Func(self.parent.setDamageNode, textNodePath),
                                            textNodePath.posInterval(1.5, end_pos, start_pos),
                                            Func(self.parent.deleteDamageNode, textNodePath)
                                            )
            damage_parallel.append(Parallel(target_anim, damage_text_sequence, Func(self.parent.parent.afterUnitShootHook, int(self.id))))
        seq.append(damage_parallel)
        # Start our shoot sequence
        shoot = Sequence(Func(self.parent.parent.beforeUnitShootHook, int(self.id)),
                         seq
                         )
        shoot.start()        

    
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
        dest_node = NodePath("dest_node")
        dest_node.setPos(render, tile_pos.getX()+0.5, tile_pos.getY()+0.5, 0.3)
        self.node.lookAt(dest_node)
        
        
    def cleanup(self):
        self.model.cleanup()
        
    def remove(self):
        self.model.remove()
    
