from panda3d.core import *
from direct.interval.IntervalGlobal import Sequence, Parallel, Func, Wait, LerpColorScaleInterval#@UnresolvedImport
from direct.showbase.DirectObject import DirectObject
import utils as utils
from share import *


class AnimationManager():
    def __init__(self, parent):
        self.parent = parent
        self._anim_in_process = False
        
        self.bullet = loader.loadModel("sphere")
        self.bullet.setScale(0.05)
        self.bullet.reparentTo(render)
        self.bullet.stash()
    
    def beforeAnimHook(self):
        self._anim_in_process = True
    
    def afterAnimHook(self):     
        self._anim_in_process = False
    
    def createSequence(self, msg_list):
        animation = Sequence()
        animation.append(Func(self.beforeAnimHook))
        unit_pos_dict = {}
        for msg in msg_list:
            #========================================================================
            #
            if msg[0] == MOVE or msg[0] == ROTATE:
                unit_id = msg[1]
                tile = msg[2]
                unit_model = self.parent.unit_renderer_dict[unit_id]
                if unit_pos_dict.has_key(unit_id):
                    start_pos = unit_pos_dict[unit_id][0]
                    start_head = unit_pos_dict[unit_id][1]
                else:
                    start_pos = unit_model.model.getPos(render)
                    start_head = unit_model.model.getH(render)
                end_pos = Point3(utils.TILE_SIZE*(tile[0] + 0.5), utils.TILE_SIZE*(tile[1] + 0.5), utils.GROUND_LEVEL)
                dummy_start = NodePath("dummy_start")
                dummy_end = NodePath("dummy_end")
                dummy_start.setPos(start_pos)
                dummy_end.setPos(end_pos)
                dummy_start.lookAt(dummy_end)
                end_head = dummy_start.getH(render)
            
                interval_heading = unit_model.model.quatInterval(0.2, hpr=Point3(end_head, 0, 0), startHpr=Point3(start_head, 0, 0))
                if msg[0] == MOVE:
                    interval_movement = unit_model.node.posInterval(0.5, end_pos, startPos=start_pos)
                    anim = Parallel(interval_movement, interval_heading)
                    unit_pos_dict[unit_id] = (end_pos, end_head)
                else:
                    anim = interval_heading
                    unit_pos_dict[unit_id] = (start_pos, end_head)
                
                animation.append(anim)
            #========================================================================
            #
            elif msg[0] == UNIT:          
                unit = msg[1]
                old_x = self.parent.parent.local_engine.units[unit['id']]['pos'][0]
                old_y = self.parent.parent.local_engine.units[unit['id']]['pos'][1]
                self.parent.parent.local_engine.refreshUnit(unit)
                if self.parent.parent.local_engine.isThisMyUnit(unit['id']):
                    self.parent.parent.interface.refreshUnitInfo(unit['id'])          
                if self.parent.parent.sel_unit_id == unit['id']:
                    self.parent.parent.interface.processUnitData( unit['id'] )                  
                    self.parent.parent.interface.printUnitData( unit['id'] )
                    self.parent.parent.movement.calcUnitAvailMove( unit['id'] )
                    self.parent.parent.render_manager.refreshEnemyUnitMarkers()
                    if unit['pos'][0] != old_x or unit['pos'][1] != old_y or unit['last_action']=='use':
                        animation.append(Func(self.parent.parent.render_manager.refreshFow))
                    #self.parent.sgm.playUnitStateAnim( unit['id'] )
            #========================================================================
            #
            elif msg[0] == SHOOT:
                shooter_id = msg[1] # unit_id of the shooter
                shoot_tile = msg[2] # (x,y) pos of targeted tile
                weapon = msg[3] # weapon id
                damage_list = msg[4] # list of all damaged/missed/bounced/killed units
                # shooter_id can be negative if we don't see the shooter
                if shooter_id >= 0:
                    shooter_unit_renderer = self.parent.unit_renderer_dict[shooter_id]
                    shoot_anim = shooter_unit_renderer.model.actorInterval('shoot')
                    shooter_pos =  Point3(utils.TILE_SIZE*(self.parent.parent.local_engine.units[shooter_id]['pos'][0] + 0.5), 
                                          utils.TILE_SIZE*(self.parent.parent.local_engine.units[shooter_id]['pos'][1] + 0.5),
                                          utils.GROUND_LEVEL
                                          )
                    # We create the bullet and its animation
                    start_pos = Point3(shooter_pos.getX(), shooter_pos.getY(), 0.6)
                    end_pos = Point3(utils.TILE_SIZE*(shoot_tile[0] + 0.5), utils.TILE_SIZE*(shoot_tile[1] + 0.5), 0.6)
                    dest_node = NodePath("dest_node")
                    dest_node.setPos(end_pos)
                    start_node = NodePath("start_node")
                    start_node.setPos(start_pos)
                    time = round(start_node.getDistance(dest_node) / utils.BULLET_SPEED, 2)
                    bullet_sequence = Sequence(Func(self.bullet.unstash),
                                               self.bullet.posInterval(time, end_pos, start_pos),
                                               Func(self.bullet.stash)
                                               )

                    damage_anim = self.buildDamageAnim(damage_list)
                    animation.append(Parallel(shoot_anim, Sequence(bullet_sequence, damage_anim)))  
            #========================================================================
            #
            elif msg[0] == SPOT:
                self.parent.parent.local_engine.units[unit['id']] = unit
                # This is the first time we see this unit, fill out starting variables for move and rotate actions
                spotted_unit_model = self.parent.loadUnit(unit['id'])
        
                pos = Point3(utils.TILE_SIZE*(self.parent.parent.local_engine.units[unit['id']]['pos'][0] + 0.5), 
                             utils.TILE_SIZE*(self.parent.parent.local_engine.units[unit['id']]['pos'][1] + 0.5),
                             utils.GROUND_LEVEL
                             )
                heading = utils.getHeadingAngle(self.parent.parent.local_engine.units[unit['id']]['heading'])
                animation.append(Func(self.parent.showUnit, unit_model, pos, None))

                self.parent.parent.local_engine.level.putUnitDict(msg[1])  
                if self.parent.parent.player_id == self.parent.parent.turn_player and self.parent.parent.sel_unit_id != None:
                    self.parent.parent.movement.calcUnitAvailMove( self.parent.parent.sel_unit_id )
                    #self.parent.sgm.showVisibleEnemies( self.parent.sel_unit_id )
            #========================================================================
            #
            elif msg[0] == VANISH:
                self._message_in_process = True            
                # Animation manager sets _message_in_process to False when the animation is done
                self.handleVanish(msg[1])
            #========================================================================
            #
            elif msg[0] == CHAT:         
                sender_name = msg[2]
                self.parent.interface.console.consoleOutput( sender_name + ":" + str(msg[1]), utils.CONSOLE_SYSTEM_MESSAGE)
                self.parent.interface.console.show()           
            #========================================================================
            #
            elif msg[0] == LEVEL:
                self.parent.parent.local_engine.old_level = self.parent.parent.local_engine.level
                level = msg[1]
                for unit in self.parent.parent.local_engine.units.itervalues():
                    level.putUnitDict(unit)
                self.parent.parent.local_engine.level = level
                # if our enemy opens doors, we need to update visibility
                # enemy's visibility gets updated when he gets UNIT message
                if self.parent.parent.player_id == self.parent.parent.turn_player and self.parent.parent.sel_unit_id != None:
                    self.parent.parent.movement.calcUnitAvailMove( self.parent.parent.sel_unit_id )

                # Create animations based on level changes (opened doors etc)    
                print self.parent.parent.local_engine.level._grid
                for x, val in enumerate(self.parent.parent.local_engine.old_level._grid):
                    for y, val2 in enumerate(val):
                        if val2 != None and self.parent.parent.local_engine.level._grid[x][y] != None:
                            if val2.name != self.parent.parent.local_engine.level._grid[x][y].name:
                                x,y,h = self.parent.level_renderer.getWallPosition(x, y)
                                model = self.parent.level_renderer.door_dict[(x,y,h)]
                                door = model.find("**/Door*")                                
                                if val2.name == 'ClosedDoor':
                                    animation.append(door.posInterval(1, Vec3(0.5,0,-0.72)))
                                elif val2.name == 'OpenedDoor':
                                    animation.append(door.posInterval(1, Vec3(0.5,0,0)))
            #========================================================================
            #
            elif msg[0] == USE:
                self.parent.unit_renderer_dict[msg[1]].model.play('use')    
            #========================================================================
            #
            elif msg[0] == TAUNT:
                self.parent.sgm.unit_np_dict[msg[1][0]].model.play('taunt')
                if msg[1][1]:
                    self.parent.handleShoot(msg[1][1]) 
            #========================================================================
            #         
            elif msg[0] == NEW_GAME_STARTED:
                self.parent.newGameStarted( msg[1] )
            #========================================================================
            #        
            else:
                self._message_in_process = True
                self.log.error("Unknown message Type: %s", msg[0])
                self._message_in_process = False
        
        animation.append(Func(self.afterAnimHook))            
        animation.start()
    
    def buildDeleteAnim(self, unit_id):
        return Sequence(Func(self.parent.hideUnit, unit_id), 
                        Wait(0.2)
                        #Func(self.parent.unit_marker_renderer.clearMarker, unit_id)
                        )
    
    def buildDetachAnim(self, unit_id):
        return Sequence(Func(self.sgm.detachUnit, unit_id), Wait(0.2))
    
    def buildLaserAnim(self, source, target):
        self.combat.source = source
        self.combat.target = target
        taskMgr.add(self.combat.drawBeam, 'beamtask')
        

    def buildMeleeAnim(self, unit_renderer, target_tile, weapon):
        # Unit melee animation
        melee_anim = unit_renderer.model.actorInterval('melee')
        return melee_anim
    
    def buildDamageAnim(self, damage_list):
        # Find all damaged units and play their damage/kill/miss animation
        damage_parallel = Parallel()
        for action in damage_list:
            damage_type = action[0]
            target_unit_id = action[1]
            target_unit_renderer = self.parent.unit_renderer_dict[target_unit_id]
            t = TextNode('dmg')
            if damage_type == "bounce":
                target_anim = target_unit_renderer.model.actorInterval('get_hit') 
                dmg = 'bounce'
            elif damage_type == "miss":
                target_anim = target_unit_renderer.model.actorInterval('get_hit') 
                dmg = 'miss'                
            elif damage_type == "damage":
                color_interval = Sequence(LerpColorScaleInterval(target_unit_renderer.model, 0.2, (10,10,10,1))
                                         ,LerpColorScaleInterval(target_unit_renderer.model, 0.2, (1,1,1,1)))
                target_anim = Parallel(target_unit_renderer.model.actorInterval('get_hit'), color_interval)
                dmg = str(action[2])
            elif damage_type == "kill":
                color_interval = Sequence(LerpColorScaleInterval(target_unit_renderer.model, 0.2, (10,10,10,1))
                                         ,LerpColorScaleInterval(target_unit_renderer.model, 0.2, (1,1,1,1)))                
                target_anim = Parallel(target_unit_renderer.model.actorInterval('die')  , color_interval)
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
            damage_text_sequence = Sequence(Func(textNodePath.reparentTo, target_unit_renderer.node),
                                            textNodePath.posInterval(1, end_pos, start_pos),
                                            Func(textNodePath.removeNode)
                                            ) 
            damage_parallel = Parallel(damage_text_sequence, target_anim)       
        return damage_parallel
    
    def handleVanish(self, unit_id):
        i = self.buildDeleteAnim(unit_id)
        s = Sequence(i)
        s.start()        
        
    def handleNewTurn(self):
        text = TextNode('new turn node')
        player_name = self.parent.parent.local_engine.getPlayerById(self.parent.parent.turn_player)
        text.setText("TURN: "+player_name)
        textnp = NodePath("textnp")
        textNodePath = textnp.attachNewNode(text)
        textNodePath.setColor(1, 0, 0)
        textNodePath.setScale(0.01, 0.01, 0.01)
        textNodePath.setPos(-0.7, 0, 0)
        textNodePath.reparentTo(aspect2d)
        s = Sequence(textNodePath.scaleInterval(.3, textNodePath.getScale()*20,blendType='easeIn'),
                     Wait(1.0),
                     textNodePath.scaleInterval(.3, textNodePath.getScale()*0.05,blendType='easeIn'),
                     Func(textNodePath.removeNode),
                     Func(self.afterAnimHook)
                     )
        s.start()     
        

    def playUnitStateAnim(self, unit_id):
        # Check if we have toggled overwatch
        unit = self.parent.units[unit_id]
        unit_model = self.unit_np_dict[unit_id]
        if unit_model.isOverwatch == False and unit['overwatch'] == True:
            unit_model.isOverwatch = True
            unit_model.fsm.request('Overwatch')
        elif unit_model.isOverwatch == True and unit['overwatch'] == False:
            unit_model.isOverwatch = False
            unit_model.fsm.request('StandUp')
        elif unit_model.isSetup == False:
            try:
                if unit['set_up'] == True:
                    unit_model.isSetup = True
                    unit_model.fsm.request('SetUp')
            except:
                None
        elif unit_model.isSetup == True:
            try:
                if unit['set_up'] == False:
                    unit_model.isSetup = False
                    unit_model.fsm.request('StandUp')
            except:
                None

        