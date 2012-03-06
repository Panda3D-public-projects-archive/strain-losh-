#############################################################################
# IMPORTS
#############################################################################

# python imports
import time

# panda3D imports
from panda3d.core import TextNode, NodePath, Point2, Point3#@UnresolvedImport
from panda3d.core import ConfigVariableString, ConfigVariableInt#@UnresolvedImport
from direct.interval.IntervalGlobal import Sequence, Parallel, Func, Wait, LerpColorScaleInterval#@UnresolvedImport
from direct.showbase.DirectObject import DirectObject
from direct.fsm import FSM


# strain related imports
from client_messaging import *
from sgm import SceneGraph
from camera import Camera
#from cam2 import Camera
from net import Net
from interface import Interface
from picker import Picker
import utils as utils
from strain.share import *
from combat import Combat

#========================================================================
#
class Client(DirectObject):
    def __init__(self, parent, player, type="Game"):
        self.parent = parent
        self.player = player
        self.player_id = None
        
        # Set up important game logic variables
        self.level = None
        self.units = {}
        self.inactive_units = {}
        self.players = {}
        self.sel_unit_id = None
        self.turn_number = None
        
        # Init Client FSM
        self.fsm = ClientFSM(self, 'ClientFSM')
        
        # Init SceneGraph manager
        self.sgm = SceneGraph(self)
        
        # Init Picker
        self.picker = Picker(self)
        
        # Init Camera
        self.camera = Camera(self, 20, 20)
        
        # Init Interface
        self.interface = Interface(self)
        
        # All of our graphics components are initialized, request graphics init
        self.fsm.request('GraphicsInit')
        
        # Init combat
        self.combat = Combat()
        
        # Init Network
        self.server_ip = ConfigVariableString("server-ip", "127.0.0.1").getValue()
        self.server_port = ConfigVariableInt("server-port", "56005").getValue()

        # Flags
        # This handles message queue - we will process messages in sync one by one
        self._message_in_process = False
        # This handles interface interactions - we will not allow interaction if current animation is not done
        self._anim_in_process = False 

        #Initialize game mode (network)
        if type == "Game":
            self.fsm.request('GameMode')
        elif type == "Replay":
            self.fsm.request('ReplayMode', "replay_2011-12-19_1.rpl")
            
        # Turn number and player on turn
        self.turn_number = 0
        self.turn_player = None
        
        self.num = 0
        taskMgr.add(self.clientTask, 'clientTask')#@UndefinedVariable
        
        self.shader = True
        self.accept('enter', self.toggleShader)
    
    def toggleShader(self):
        if self.shader:
            self.sgm.level_mesh.node_wall_usable.setShaderOff()
            self.shader = False
        else:
            self.sgm.level_mesh.node_wall_usable.setShaderAuto()
            self.shader = True
    
    def clientTask(self, task):
        #self.num += 1
        #print self.num
        return task.cont
    
    def newTurn(self):
        self.deselectUnit()
        
    def getPlayerName(self, player_id):
        for p in self.players:
            if p['id'] == player_id:
                return p['name']
    
    def deselectUnit(self):
        self.clearState()
        
    def selectUnit(self, unit_id):
        if self._anim_in_process == True:
            return
        
        if not self.units.has_key(unit_id):
            return
        
        if self.sel_unit_id != unit_id:
            self.deselectUnit()
            self.sel_unit_id = unit_id
            self.sgm.loadAltRenderModel(unit_id)
            self.interface.refreshUnitData(unit_id) 
            # If it is our turn, display available move tiles
            if self.player == self.turn_player:
                self.sgm.unit_np_dict[unit_id].setSelected()
                self.picker.calcUnitAvailMove(unit_id)
                self.sgm.showVisibleEnemies(unit_id)
                #self.sgm.unit_np_dict[unit_id].setCollisionOff()
            
    def selectNextUnit(self):
        if self.sel_unit_id == None:
            last = 0
        else:
            last = self.sel_unit_id
        
        d = {}
        for unit_id in self.units.iterkeys():
            if self.isThisMyUnit(unit_id):
                d[unit_id] = self.units[unit_id]
        
        l = sorted(d.iterkeys())
        if len(l) <= 1:
            return
        else:
            if l[-1] == last:
                new_unit_id = l[0]
            else:
                for i in l:
                    if i > last:
                        new_unit_id = i
                        break
            self.selectUnit(new_unit_id)
        
    def selectPrevUnit(self):
        if self.sel_unit_id == None:
            # TODO: ogs: Kaj fakat?
            last = 9999999
        else:
            last = self.sel_unit_id
            
        d = {}
        for unit_id in self.units.iterkeys():
            if self.isThisMyUnit(unit_id):
                d[unit_id] = self.units[unit_id]
        
        l = sorted(d.iterkeys())
        l.reverse()
        if len(l) <= 1:
            return
        else:
            if l[-1] == last:
                new_unit_id = l[0]
            else:
                for i in l:
                    if i < last:
                        new_unit_id = i
                        break
            self.selectUnit(new_unit_id)
    
    def refreshUnit(self, unit):
        if unit['alive'] == False:
            if self.sel_unit_id == unit['id']:
                self.sel_unit_id = None
            if self.sgm.unit_np_dict.has_key(unit['id']):
                self.sgm.hideUnit(unit['id'])
            if self.units.has_key(unit['id']):
                if self.isThisMyUnit(unit['id']):
                    self.inactive_units[unit['id']] = unit
                self.deleteUnit(unit['id'])
            self.level.removeUnitDict(unit)
        else:
            self.units[unit['id']] = unit
            self.level.removeUnitId(unit['id'])
            self.level.putUnitDict(unit)
    
    def deleteUnit(self, unit_id):
        self.level.removeUnitId(unit_id)
        self.units.pop(unit_id)
    
    def getUnitData(self, unit_id):
        if self.units.has_key(unit_id):
            return self.units[unit_id]
    
    def isThisMyUnit(self, unit_id):
        if self.units[unit_id]['owner_id'] == self.player_id:
            return True
        else:
            return False
    
    def isThisEnemyUnit(self, unit_id):
        if self.units[unit_id]['owner_id'] != self.player_id:
            return True
        else:
            return False
        
    def isUnitAlive(self, unit_id):
        return self.units[unit_id]['alive']
    
    def getCoordsByUnit(self, unit_id):
        if self.units.has_key(unit_id):
            unit = self.units[unit_id]
        return Point2(unit['pos'][0], unit['pos'][1])
    
    def getUnitByCoords(self, pos):
        for u in self.units.itervalues():
            if u['pos'][0] == pos.getX() and u['pos'][1] == pos.getY():
                return u['id']
        return None
    
    def beforeAnimHook(self):
        self._anim_in_process = True
        self.sgm.hideUnitAvailMove()
        self.sgm.hideVisibleEnemies()
        for u in self.sgm.unit_np_dict.itervalues():
            u.clearTargeted()
        self.picker.hovered_unit_id = None
            
    
    def afterAnimHook(self):     
        self._anim_in_process = False
        self._message_in_process = False
        
    def endTurn(self):
        ClientMsg.endTurn()
    
    def clearState(self):
        self.sgm.clearAltRenderModel()
        #self.sgm.hideUnitAvailMove()
        self.sgm.hideVisibleEnemies()
        self.interface.clearUnitData()
        
        if self.sel_unit_id != None:
            self.sgm.unit_np_dict[self.sel_unit_id].clearAllFlags()
            #self.sgm.unit_np_dict[self.sel_unit_id].setCollisionOn()
        self.sel_unit_id = None
    
#========================================================================
# Client animation handler methods
    def handleMove(self, move_msg):
        move = self.buildMove(move_msg)
        s = Sequence(Func(self.beforeAnimHook), move, Func(self.afterAnimHook))
        s.start()
    
    def buildMove(self, move_msg):
        unit_id = move_msg[0]
        action_list = move_msg[1]
        
        pos = None
        heading = None
        unit_model = None
        
        s = Sequence()
        d = 0.0
        
        if self.units.has_key(unit_id):
            pos = Point3(self.units[unit_id]['pos'][0] + utils.MODEL_OFFSET, self.units[unit_id]['pos'][1] + utils.MODEL_OFFSET, utils.GROUND_LEVEL)
            heading = utils.getHeadingAngle(self.units[unit_id]['heading'])
            if self.sgm.unit_np_dict.has_key(unit_id):
                unit_model = self.sgm.unit_np_dict[unit_id]
        else:
            # This is the first time we see this unit, we have no record of it in client.units dict or sgm nodepath list and dict
            # First action we MUST receive here is 'spot', otherwise client will break as we dont have unit_model defined
            None
            
        for idx, action in enumerate(action_list):
            action_type = action[0]
            if action_type == "move":
                end_pos = Point3(action[1][0] + utils.MODEL_OFFSET, action[1][1] + utils.MODEL_OFFSET, utils.GROUND_LEVEL)
                i, duration, pos, heading = self.buildMoveAnim(unit_model, pos, end_pos, heading)
                d += duration
                s.append(i)
            elif action_type == "rotate":
                end_pos = Point3(action[1][0] + utils.MODEL_OFFSET, action[1][1] + utils.MODEL_OFFSET, utils.GROUND_LEVEL)
                i, duration, pos, heading = self.buildRotateAnim(unit_model, pos, end_pos, heading)
                d += duration
                s.append(i)
            elif action_type == "spot":
                spotted_unit = action[1]
                self.units[spotted_unit['id']] = spotted_unit
                # Check if we have this unit in our scene graph records
                if self.sgm.unit_np_dict.has_key(spotted_unit['id']):
                    spotted_unit_model = self.sgm.unit_np_dict[spotted_unit['id']]
                # This is the first time we see this unit, fill out starting variables for move and rotate actions
                else:
                    wpn_list = utils.getUnitWeapons(spotted_unit)
                    spotted_unit_model = self.sgm.loadUnit(spotted_unit['id'], wpn_list)
                
                # If this is our move message, means we spotted an enemy, and he will not be moving
                # If this is enemy move message, means we have spotted a moving enemy and we will set unit_model variable
                if self.isThisEnemyUnit(unit_id):
                    unit_model = spotted_unit_model
                    pos = Point3(self.units[spotted_unit['id']]['pos'][0] + utils.MODEL_OFFSET, 
                                 self.units[spotted_unit['id']]['pos'][1] + utils.MODEL_OFFSET,
                                 utils.GROUND_LEVEL
                                 )
                    heading = utils.getHeadingAngle(self.units[spotted_unit['id']]['heading'])
                    spotted_pos = pos
                    spotted_h = heading
                else:
                    spotted_pos = None
                    spotted_h = None
                i = self.buildSpotAnim(spotted_unit_model, spotted_pos, spotted_h)
                s.append(i)
            elif action_type == "vanish":
                vanish_unit_id = action[1]
                spotted_later = False
                for a in action_list[idx:]:
                    if a[0] == "spot":
                        spotted_later = True
                        break
                if spotted_later:
                    i = self.buildDetachAnim(vanish_unit_id)
                else:
                    i = self.buildDeleteAnim(vanish_unit_id)
                s.append(i)
            elif action_type == "overwatch":
                action_list = action[1]
                i = self.buildOverwatchAnim(action_list)
                s.append(i)
        
        anim = unit_model.model.actorInterval('walk', loop = 1, duration = d)
        anim_end = unit_model.model.actorInterval('idle', startFrame=1, endFrame=1)
        move = Sequence(Parallel(anim, s), Sequence(anim_end))
        return move
        
    def buildMoveAnim(self, unit_model, start_pos, end_pos, start_h):
        dummy_start = NodePath("dummy_start")
        dummy_end = NodePath("dummy_end")
        duration = 0.0
        p = None   
        dummy_start.setPos(start_pos)
        dummy_end.setPos(end_pos)
        dummy_start.lookAt(dummy_end) 
        end_h = dummy_start.getH(render)               
        # Model heading is different than movement heading, first create animation that turns model to his destination
        i_h = None
        if end_h != start_h:
            i_h = unit_model.model.quatInterval(0.2, hpr = Point3(end_h, 0, 0), startHpr = Point3(start_h, 0, 0))
        i = unit_model.node.posInterval(0.5, end_pos, start_pos)
        duration += 0.5
        if i_h:
            p = Parallel(i, i_h)
        else:
            p = i
        return p, duration, end_pos, end_h  
    
    def buildRotateAnim(self, unit_model, start_pos, end_pos, start_h, heading=None):
        if heading == None:
            dummy_start = NodePath("dummy_start")
            dummy_end = NodePath("dummy_end")
            dummy_start.setPos(start_pos)
            dummy_end.setPos(end_pos)
            dummy_start.lookAt(dummy_end)
            end_h = dummy_start.getH(render)
        else:
            end_h = utils.getHeadingAngle(heading)
        interval = unit_model.model.quatInterval(0.2, hpr = Point3(end_h, 0, 0), startHpr = Point3(start_h, 0, 0))
        duration = 0.2
        return interval, duration, start_pos, end_h          
    
    def buildSpotAnim(self, unit_model, pos, heading):
        return Sequence(Func(self.sgm.showUnit, unit_model, pos, None)
                       ,Wait(0.2)
                       ,Func(self.interface.console.consoleOutput, 'Unit spotted!', utils.CONSOLE_SYSTEM_MESSAGE)
                       ,Func(self.interface.console.show)
                       )
    
    def buildDeleteAnim(self, unit_id):
        return Sequence(Func(self.sgm.hideUnit, unit_id), Func(self.deleteUnit, unit_id), Wait(0.2))
    
    def buildDetachAnim(self, unit_id):
        return Sequence(Func(self.sgm.detachUnit, unit_id), Wait(0.2))
    
    def buildOverwatchAnim(self, action_list):
        i = self.buildShoot(action_list)
        return i
    
    def handleShoot(self, action_list):
        shoot = self.buildShoot(action_list)
        s = Sequence(Func(self.beforeAnimHook), Wait(0.2), shoot, Func(self.afterAnimHook))
        s.start()        
    
    def buildShoot(self, action_list):
        s = Sequence()
        d = 0.0
        for action in action_list:
            action_type = action[0]
            
            if action_type == "shoot":
                shooter_id = action[1] # unit_id of the shooter
                shoot_tile = action[2] # (x,y) pos of targeted tile
                weapon = action[3] # weapon id
                damage_list = action[4] # list of all damaged/missed/bounced/killed units
                if shooter_id >= 0:
                    shooter_model = self.sgm.unit_np_dict[shooter_id]
                    a = self.buildShootAnim(shooter_model, weapon)
                    shooter_pos =  Point3(self.units[shooter_id]['pos'][0] + utils.MODEL_OFFSET, 
                                          self.units[shooter_id]['pos'][1] + utils.MODEL_OFFSET,
                                          utils.GROUND_LEVEL
                                          )
                    b = self.buildBulletAnim(shooter_pos, shoot_tile)
                    i = self.buildDamageAnim(damage_list)
                    bi = Sequence(b, i)
                    s.append(Parallel(a, bi))                    
            #if action_type == "shoot":
            #    shooter_id = action[1] # unit_id of the shooter
            #    shoot_tile = action[2] # (x,y) pos of targeted tile
            #    weapon = action[3] # weapon id
            #    damage_list = action[4] # list of all damaged/missed/bounced/killed units
            #    if shooter_id >= 0:
            #        shooter_model = self.sgm.unit_np_dict[shooter_id]
            #        a = self.buildShootAnim(shooter_model, weapon)
            #        b = Sequence(Func(self.buildLaserAnim, shooter_model.node, self.sgm.unit_np_dict[damage_list[0][1]].node))
            #        i = self.buildDamageAnim(damage_list)
            #        bi = Sequence(b, i)
            #        s.append(Parallel(a, bi))

            elif action_type == "melee":
                shooter_id = action[1] # unit_id of the shooter
                shoot_tile = action[2] # (x,y) pos of targeted tile
                weapon = action[3] # weapon id
                damage_list = action[4] # list of all damaged/missed/bounced/killed units
                shooter_model = self.sgm.unit_np_dict[shooter_id]
                i = self.buildMeleeAnim(shooter_model, shoot_tile, weapon)
                s.append(i)
                i = self.buildDamageAnim(damage_list)
                s.append(i)
            elif action_type == "rotate":
                unit_id = action[1]
                heading = action[2]
                unit_model = self.sgm.unit_np_dict[unit_id]
                start_h = utils.getHeadingAngle(self.units[unit_id]['heading'])
                i, duration, pos, h = self.buildRotateAnim(unit_model, None, None, start_h, heading)
                s.append(i)
            elif action_type == "overwatch":
                action_list = action[1]
                i = self.buildOverwatchAnim(action_list)
                s.append(i)
        
        # Start our shoot sequence
        return s
    
    def buildShootAnim(self, unit_model, weapon):
        # Unit shooting animation
        shoot_anim = unit_model.model.actorInterval('shoot')
        return shoot_anim
    
    def buildBulletAnim(self, start_pos, target_tile):
        # We create the bullet and its animation
        self.bullet = loader.loadModel("sphere")
        self.bullet.setScale(0.05)
        start_pos = Point3(start_pos.getX(), start_pos.getY(), 0.9)
        end_pos = Point3(target_tile[0] + utils.MODEL_OFFSET, target_tile[1] + utils.MODEL_OFFSET, 0.9)
        dest_node = NodePath("dest_node")
        dest_node.setPos(end_pos)
        start_node = NodePath("start_node")
        start_node.setPos(start_pos)
        time = round(start_node.getDistance(dest_node) / utils.BULLET_SPEED, 2)
        bullet_sequence = Sequence(Func(self.sgm.setBullet, self.bullet),
                                   self.bullet.posInterval(time, end_pos, start_pos),
                                   Func(self.sgm.deleteBullet, self.bullet)
                                   )
        return bullet_sequence
    
    def buildLaserAnim(self, source, target):
        self.combat.source = source
        self.combat.target = target
        taskMgr.add(self.combat.drawBeam, 'beamtask')
        

    def buildMeleeAnim(self, unit_model, target_tile, weapon):
        # Unit melee animation
        melee_anim = unit_model.model.actorInterval('melee')
        return melee_anim
    
    def buildDamageAnim(self, damage_list):
        # Find all damaged units and play their damage/kill/miss animation
        damage_parallel = Parallel()
        for action in damage_list:
            damage_type = action[0]
            target_unit_id = action[1]
            target_unit = self.sgm.unit_np_dict[target_unit_id]
            t = TextNode('dmg')
            if damage_type == "bounce":
                target_anim = target_unit.model.actorInterval("get_hit")
                dmg = 'bounce'
            elif damage_type == "miss":
                target_anim = target_unit.model.actorInterval("get_hit")
                dmg = 'miss'                
            elif damage_type == "damage":
                color_interval = Sequence(LerpColorScaleInterval(target_unit.model, 0.2, (10,10,10,1))
                                         ,LerpColorScaleInterval(target_unit.model, 0.2, (1,1,1,1)))
                target_anim = Parallel(target_unit.model.actorInterval("get_hit"), color_interval)
                dmg = str(action[2])
            elif damage_type == "kill":
                color_interval = Sequence(LerpColorScaleInterval(target_unit.model, 0.2, (10,10,10,1))
                                         ,LerpColorScaleInterval(target_unit.model, 0.2, (1,1,1,1)))                
                target_anim = Parallel(target_unit.model.actorInterval("die"), color_interval)
                dmg = str(action[2])
            t.setText( "%s" % dmg)
            t.setTextColor(1, 0, 0, 1)
            t.setAlign(TextNode.ACenter)
            textNodePath = NodePath("textnp")
            textNodePath.attachNewNode(t)
            textNodePath.setScale(0.35)
            textNodePath.setBillboardPointEye()
            textNodePath.setLightOff()
            # textNodePath will be reparented to unitmodel, so set start and end pos relative to the unit
            start_pos = Point3(0, 0, 0.9)
            end_pos = start_pos + Point3(0, 0, 3)
            damage_text_sequence = Sequence(Func(self.sgm.setDamageNode, textNodePath, target_unit.node),
                                            textNodePath.posInterval(1, end_pos, start_pos),
                                            Func(self.sgm.deleteDamageNode, textNodePath)
                                            ) 
            damage_parallel = Parallel(damage_text_sequence, target_anim)       
        return damage_parallel
    
    def handleVanish(self, unit_id):
        i = self.buildDeleteAnim(unit_id)
        s = Sequence(i, Func(self.afterAnimHook))
        s.start()
        
    def handleSpot(self, unit):
        self.units[unit['id']] = unit
        # This is the first time we see this unit, fill out starting variables for move and rotate actions
        wpn_list = utils.getUnitWeapons(unit)
        spotted_unit_model = self.sgm.loadUnit(unit['id'], wpn_list)

        pos = Point3(self.units[unit['id']]['pos'][0] + utils.MODEL_OFFSET, 
                     self.units[unit['id']]['pos'][1] + utils.MODEL_OFFSET,
                     utils.GROUND_LEVEL
                     )
        heading = utils.getHeadingAngle(self.units[unit['id']]['heading'])
        i = self.buildSpotAnim(spotted_unit_model, pos, heading)
        s = Sequence(i, Func(self.afterAnimHook))
        s.start()        
        
    def handleNewTurn(self):
        self.sgm.level_mesh.setInvisibleTiles(self.getInvisibleTiles())
        text = TextNode('new turn node')
        text.setText("TURN: "+self.turn_player)
        textnp = NodePath("textnp")
        textNodePath = textnp.attachNewNode(text)
        textNodePath.setColor(1, 0, 0)
        textNodePath.setScale(0.01, 0.01, 0.01)
        textNodePath.setPos(-0.7, 0, 0)
        textNodePath.reparentTo(aspect2d)
        s = Sequence(textNodePath.scaleInterval(.3, textNodePath.getScale()*20,blendType='easeIn'),
                     Wait(1.0),
                     textNodePath.scaleInterval(.3, textNodePath.getScale()*0.05,blendType='easeIn'),
                     Func(self.sgm.deleteTurnNode, textNodePath),
                     Func(self.afterAnimHook)
                     )
        s.start()
        
    def getInvisibleTiles(self):
        a = []
        for u in self.units:
            if self.isThisMyUnit(u):
                a.append(self.units[u])
        t = time.clock()
        l = levelVisibilityDict(a, self.level)
        print "timer:::", (time.clock()-t)*1000
        return l

#========================================================================
#
class ClientFSM(FSM.FSM):
    def __init__(self, parent, name):
        FSM.FSM.__init__(self, name)
        self.parent = parent

    def enterReplayMode(self, replay):
        self.parent.net = Net(self.parent)
        self.parent.net.startReplay(replay)
        
    def exitReplayMode(self):
        None

    def enterGameMode(self):
        self.parent.net = Net(self.parent)
        self.parent.net.startNet()
    
    def exitGameMode(self):
        None

    def enterGraphicsInit(self):
        self.parent.sgm.initLights()
        self.parent.sgm.initAltRender()
    
    def exitGraphicsInit(self):
        None