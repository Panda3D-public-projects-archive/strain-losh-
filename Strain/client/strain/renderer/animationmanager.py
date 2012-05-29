from panda3d.core import *
from direct.interval.IntervalGlobal import Sequence, Parallel, Func, Wait, LerpColorScaleInterval#@UnresolvedImport
from direct.showbase.DirectObject import DirectObject
import strain.utils as utils

class AnimationManager():
    def __init__(self, parent):
        self.parent = parent
        self._anim_in_process = False
        
    
    def beforeAnimHook(self):
        self._anim_in_process = True
        self.parent.parent.movement.deleteUnitAvailMove()
        #self.sgm.hideVisibleEnemies()
        #for u in self.sgm.unit_np_dict.itervalues():
        #    u.clearTargeted()
        #self.movement.hovered_unit_id = None
    
    def afterAnimHook(self):     
        self._anim_in_process = False
        self.parent.parent.parent.net_manager._message_in_process = False
    
    
    def handleMove(self, move_msg):
        move = self.buildMove(move_msg)
        s = Sequence(Func(self.beforeAnimHook), 
                     move, 
                     Func(self.afterAnimHook)
                     )
        s.start()
    
    def buildMove(self, move_msg):
        unit_id = move_msg[0]
        action_list = move_msg[1]
        
        pos = None
        heading = None
        unit_model = None
        
        s = Sequence()
        d = 0.0
        
        if self.parent.parent.local_engine.units.has_key(unit_id):
            pos = Point3(utils.TILE_SIZE*(self.parent.parent.local_engine.units[unit_id]['pos'][0] + 0.5), 
                         utils.TILE_SIZE*(self.parent.parent.local_engine.units[unit_id]['pos'][1] + 0.5), 
                         utils.GROUND_LEVEL)
            heading = utils.getHeadingAngle(self.parent.parent.local_engine.units[unit_id]['heading'])
            if self.parent.unit_renderer_dict.has_key(unit_id):
                unit_renderer = self.parent.unit_renderer_dict[unit_id]
        else:
            # This is the first time we see this unit, we have no record of it in client.units dict or sgm nodepath list and dict
            # First action we MUST receive here is 'spot', otherwise client will break as we dont have unit_model defined
            None
            
        for idx, action in enumerate(action_list):
            action_type = action[0]
            if action_type == "move":
                end_pos = Point3(utils.TILE_SIZE*(action[1][0] + 0.5), 
                                 utils.TILE_SIZE*(action[1][1] + 0.5), 
                                 utils.GROUND_LEVEL)
                i, duration, pos, heading = self.buildMoveAnim(unit_renderer, pos, end_pos, heading)
                d += duration
                s.append(i)
            elif action_type == "rotate":
                end_pos = Point3(utils.TILE_SIZE*(action[1][0] + 0.5), 
                                 utils.TILE_SIZE*(action[1][1] + 0.5), 
                                 utils.GROUND_LEVEL)
                i, duration, pos, heading = self.buildRotateAnim(unit_renderer, pos, end_pos, heading)
                d += duration
                s.append(i)
            elif action_type == "spot":
                spotted_unit = action[1]
                self.parent.parent.local_engine.units[spotted_unit['id']] = spotted_unit
                # Check if we have this unit in our scene graph records
                if self.parent.unit_renderer_dict.has_key(spotted_unit['id']):
                    spotted_unit_renderer = self.parent.unit_renderer_dict[spotted_unit['id']]
                # This is the first time we see this unit, fill out starting variables for move and rotate actions
                else:
                    spotted_unit_renderer = self.parent.loadUnit(spotted_unit['id'])
                
                # If this is our move message, means we spotted an enemy, and he will not be moving
                # If this is enemy move message, means we have spotted a moving enemy and we will set unit_model variable
                if self.parent.parent.local_engine.isThisEnemyUnit(unit_id):
                    unit_model = spotted_unit_renderer
                    pos = Point3(utils.TILE_SIZE*(self.parent.parent.local_engine.units[spotted_unit['id']]['pos'][0] + 0.5), 
                                 utils.TILE_SIZE*(self.parent.parent.local_engine.units[spotted_unit['id']]['pos'][1] + 0.5),
                                 utils.GROUND_LEVEL
                                 )
                    heading = utils.getHeadingAngle(self.parent.parent.local_engine.units[spotted_unit['id']]['heading'])
                    spotted_pos = pos
                    spotted_h = heading
                else:
                    spotted_pos = None
                    spotted_h = None
                i = self.buildSpotAnim(spotted_unit_renderer, spotted_pos, spotted_h)
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
        
        anim = unit_renderer.model.actorInterval('walk', loop = 1, duration = d)
        anim_end = unit_renderer.model.actorInterval('idle', startFrame=1, endFrame=1)
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
        return Sequence(Func(self.parent.showUnit, unit_model, pos, None)
                       ,Wait(0.2)
                       #,Func(self.interface.setMarker, unit_model.id)
                       #,Func(self.interface.console.consoleOutput, 'Unit spotted!', utils.CONSOLE_SYSTEM_MESSAGE)
                       #,Func(self.interface.console.show)
                       )
    
    def buildDeleteAnim(self, unit_id):
        return Sequence(Func(self.interface.clearMarker, unit_id), Func(self.sgm.hideUnit, unit_id), Func(self.deleteUnit, unit_id), Wait(0.2))
    
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
                    shooter_pos =  Point3(utils.TILE_SIZE*(self.units[shooter_id]['pos'][0] + 0.5), 
                                          utils.TILE_SIZE*(self.units[shooter_id]['pos'][1] + 0.5),
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
        shoot_anim = Func(unit_model.fsm.request, 'Shoot')
        return shoot_anim
    
    def buildBulletAnim(self, start_pos, target_tile):
        # We create the bullet and its animation
        self.bullet = loader.loadModel("sphere")
        self.bullet.setScale(0.05)
        start_pos = Point3(start_pos.getX(), start_pos.getY(), 0.9)
        end_pos = Point3(utils.TILE_SIZE*(target_tile[0] + 0.5), utils.TILE_SIZE*(target_tile[1] + 0.5), 0.9)
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
        melee_anim = Func(unit_model.fsm.request, 'Melee')
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
                target_anim = Func(target_unit.fsm.request, 'GetHit') 
                dmg = 'bounce'
            elif damage_type == "miss":
                target_anim = Func(target_unit.fsm.request, 'GetHit') 
                dmg = 'miss'                
            elif damage_type == "damage":
                color_interval = Sequence(LerpColorScaleInterval(target_unit.model, 0.2, (10,10,10,1))
                                         ,LerpColorScaleInterval(target_unit.model, 0.2, (1,1,1,1)))
                target_anim = Sequence(Func(target_unit.fsm.request, 'GetHit') , color_interval)
                dmg = str(action[2])
            elif damage_type == "kill":
                color_interval = Sequence(LerpColorScaleInterval(target_unit.model, 0.2, (10,10,10,1))
                                         ,LerpColorScaleInterval(target_unit.model, 0.2, (1,1,1,1)))                
                target_anim = Parallel(Func(target_unit.fsm.request, 'Die') , color_interval)
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
        self.parent.parent.local_engine.units[unit['id']] = unit
        # This is the first time we see this unit, fill out starting variables for move and rotate actions
        spotted_unit_model = self.parent.loadUnit(unit['id'])

        pos = Point3(utils.TILE_SIZE*(self.parent.parent.local_engine.units[unit['id']]['pos'][0] + 0.5), 
                     utils.TILE_SIZE*(self.parent.parent.local_engine.units[unit['id']]['pos'][1] + 0.5),
                     utils.GROUND_LEVEL
                     )
        heading = utils.getHeadingAngle(self.parent.parent.local_engine.units[unit['id']]['heading'])
        i = self.buildSpotAnim(spotted_unit_model, pos, heading)
        s = Sequence(i, Func(self.afterAnimHook))
        s.start()        
        
    def handleNewTurn(self):
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
        