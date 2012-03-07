#############################################################################
# IMPORTS
#############################################################################

# python imports

# panda3D imports
from direct.showbase import DirectObject
from panda3d.core import NodePath, TextNode, Point3, Point2, Vec3
from direct.gui.OnscreenText import OnscreenText
from direct.interval.IntervalGlobal import Sequence, Parallel, LerpColorInterval, LerpScaleInterval#@UnresolvedImport

# strain related imports
import strain.utils as utils
from share import *
from client_messaging import *


class Movement(DirectObject.DirectObject):      
    def __init__(self, parent):
        self.parent = parent
      
        self.hovered_unit_id = None
        self.hovered_tile = None
        self.hovered_compass_tile = None
        
        self.mouse_node = aspect2d.attachNewNode('mouse_node')
        self.move_node = aspect2d.attachNewNode('move_node')
        self.move_np_list = []
        self.target_info_node = None
        
        self.accept("mouse1", self.mouseLeftClick)
        self.accept("mouse1-up", self.mouseLeftClickUp)        
    
        #taskMgr.add(self.rayupdate, 'rayupdate_task')
        taskMgr.add(self.pickerTask, 'picker_task')
        taskMgr.add(self.positionTask, 'position_task')
        
        self.color_scale_parallel = None
        
        # Create movement compass nodes
        self.turn_node = NodePath('turn_node')  
        self.turn_node.setTag('show', '0')      
        self.turn_np_list = []         
        for i in xrange(9):
            text = TextNode('node name')
            text.setAlign(TextNode.ACenter)                
            if i == 0:
                text.setText('NW')
                key = utils.HEADING_NW
            elif i == 1:
                text.setText('N')
                key = utils.HEADING_N                
            elif i == 2:
                text.setText('NE')
                key = utils.HEADING_NE                
            elif i == 3:
                text.setText('W')
                key = utils.HEADING_W                
            elif i == 4:
                text.setText('E')
                key = utils.HEADING_E                
            elif i == 5:
                text.setText('SW')
                key = utils.HEADING_SW                
            elif i == 6:
                text.setText('S')
                key = utils.HEADING_S                
            elif i == 7:
                text.setText('SE')   
                key = utils.HEADING_SE
            elif i == 8:
                text.setText('X')
                key = utils.HEADING_NONE
            textNodePath = self.turn_node.attachNewNode(text)
            textNodePath.setColor(1, 1, 1)
            textNodePath.setScale(0.05)
            textNodePath.setTag('key', str(key)) 
            self.turn_np_list.append(textNodePath) 
    
    def calcUnitAvailMove(self, unit_id):
        """Displays visual indicator of tiles which are in movement range of the selected unit."""
        self.deleteUnitAvailMove()
        unit = self.parent.units[unit_id]
        if self.parent.turn_player != self.parent.player:
            return
        if unit:
            unit['move_dict'] = getMoveDict(unit, self.parent.level, self.parent.units)
            self.parent.units[unit_id]['move_dict'] = unit['move_dict']
            move_dict = unit['move_dict']
            for tile in move_dict:
                text = TextNode('node name')
                text.setText( "%s" % move_dict[tile])
                text.setAlign(TextNode.ACenter)
                #text.setCardColor(0.2, 0.2, 0.2, 0.4)
                #text.setCardAsMargin(0, 0, 0, 0)
                textNodePath = self.move_node.attachNewNode(text)
                textNodePath.setColor(1, 1, 1)
                textNodePath.setScale(0.05)    
                textNodePath.setPythonTag('pos', tile)
                pos2d = utils.pointCoordIn2d(Point3(tile[0]+0.5, tile[1]+0.5, utils.GROUND_LEVEL))
                textNodePath.setPos(pos2d)            
                self.move_np_list.append(textNodePath)
        self.move_node.reparentTo(aspect2d)
        self.hovered_tile = None
                
    def deleteUnitAvailMove(self):
        self.move_node.detachNode() 
        for c in self.move_np_list:
            c.removeNode()
        self.move_np_list = []    
            
    def showMoveCompass(self, dest):
        # Calculate postion of compass nodes based on destination tile
        for i in self.turn_np_list:
            i.setPythonTag('pos', utils.getHeadingTile(i.getTag('key'), dest))
        # Show compass nodes
        self.turn_node.reparentTo(aspect2d)
        self.turn_node.setPythonTag('pos', dest)
        self.turn_node.setTag('show', '1')
        
        # Hide move nodes
        self.move_node.detachNode()
        
    def hideMoveCompass(self):
        # Hide compass nodes
        self.turn_node.detachNode()
        self.turn_node.setTag('show', '0')
        if self.hovered_compass_tile != None:
            self.hovered_compass_tile.setColor(1, 1, 1)
            self.hovered_compass_tile.setScale(0.05)
            self.color_scale_parallel.pause()
            self.hovered_compass_tile = None
    
    def showTargetInfo(self, node):
        shooter = self.parent.units[self.parent.sel_unit_id]
        target = self.parent.units[int(node.id)]    
        hit, desc = toHit(shooter, target, self.parent.level)
        text = str(hit)  + '%\n' + str(desc)
        if hit < 35:
            bg = (1,0,0,0.7)
            fg = (1,1,1,1)
        elif hit >= 35 and hit < 75:
            bg = (0.89, 0.82, 0.063, 0.7)
            fg = (0,0,0,1)
        elif hit >= 75:
            bg = (0.153, 0.769, 0.07, 0.7)
            fg = (0,0,0,1)
        else:
            bg = (1,0,0,0.7)
            fg = (1,1,1,1)
        self.target_info_node = aspect2d.attachNewNode('target_info')
        OnscreenText(parent = self.target_info_node
                          , text = text
                          , align=TextNode.ACenter
                          , scale=0.04
                          , fg = fg
                          , bg = bg
                          , font = loader.loadFont(utils.GUI_FONT)
                          , shadow = (0, 0, 0, 1))
    
    def clearTargetInfo(self):
        if self.target_info_node:
            self.target_info_node.removeNode()
            self.target_info_node = None
        
    def mouseLeftClick(self):
        if self.parent.interface.hovered_gui != None:
            return
        
        if self.hovered_unit_id != None:
            unit_id = int(self.hovered_unit_id)
            pickedCoord = self.parent.getCoordsByUnit(unit_id) 
            # Player can only select his own units
            if self.parent.isThisMyUnit(unit_id):
                if unit_id != self.parent.sel_unit_id:
                    self.parent.selectUnit(unit_id)
                else:
                    # Remember movement tile so we can send orientation message when mouse is depressed
                    # Do this only if it is our turn
                    if self.parent.player == self.parent.turn_player:
                        self.unit_move_destination = pickedCoord   
                        self.showMoveCompass(self.unit_move_destination)                       
            elif self.parent.isThisEnemyUnit(unit_id):
                if self.parent.sel_unit_id != None and self.parent.player == self.parent.turn_player:
                    self.parent.sgm.unit_np_dict[self.parent.sel_unit_id].target_unit = self.parent.sgm.unit_np_dict[unit_id]
                    if self.parent._anim_in_process == False:
                        ClientMsg.shoot(self.parent.sel_unit_id, unit_id)
        
        elif self.hovered_tile != None:
            if self.parent.sel_unit_id != None and self.parent.player == self.parent.turn_player:
                # Remember movement tile so we can send movement message when mouse is depressed
                # Do this only if it is our turn
                move_coord = self.hovered_tile.getPythonTag('pos')
                if self.parent.units[self.parent.sel_unit_id]['move_dict'].has_key(move_coord):
                    self.unit_move_destination = move_coord
                    self.showMoveCompass(self.unit_move_destination)


    def mouseLeftClickUp(self):
        """Handles left mouse click actions when mouse button is depressed.
           Used for unit movement.
        """
        o = None
        if self.hovered_compass_tile != None:
            x = self.turn_node.getPythonTag('pos')[0]
            y = self.turn_node.getPythonTag('pos')[1]
            orientation = int(self.hovered_compass_tile.getTag('key'))
            if orientation == utils.HEADING_NW:
                o = Point2(x-1, y+1)
            elif orientation == utils.HEADING_N:
                o = Point2(x, y+1)
            elif orientation == utils.HEADING_NE:
                o = Point2(x+1, y+1)
            elif orientation == utils.HEADING_W:
                o = Point2(x-1, y)
            elif orientation == utils.HEADING_E:
                o = Point2(x+1, y)
            elif orientation == utils.HEADING_SW:
                o = Point2(x-1, y-1)
            elif orientation == utils.HEADING_S:
                o = Point2(x, y-1)
            elif orientation == utils.HEADING_SE:
                o = Point2(x+1, y-1)
            else:
                o = None
            
        self.hideMoveCompass()
        if o != None:
            ClientMsg.move(self.parent.sel_unit_id, (x, y), (o.x, o.y))       
        
    def positionTask(self, task):
        # If turn node is displayed, you have to cancel turning or turn to be able to pick another unit or another tile to move to
        if self.turn_node.getTag('show') == '1':
            for tile in self.turn_np_list:
                pos = Point3(tile.getPythonTag('pos')[0]+0.5, tile.getPythonTag('pos')[1]+0.5, utils.GROUND_LEVEL)
                pos2d = utils.pointCoordIn2d(pos)
                tile.setPos(pos2d)        
        else:
            for unit_id in self.parent.sgm.unit_np_dict:
                u = self.parent.sgm.unit_np_dict[unit_id]
                p = utils.nodeCoordIn2d(u.model)
                u.node_2d.setPos(p)
            for tile in self.move_np_list:
                pos = Point3(tile.getPythonTag('pos')[0]+0.5, tile.getPythonTag('pos')[1]+0.5, utils.GROUND_LEVEL)
                pos2d = utils.pointCoordIn2d(pos)
                tile.setPos(pos2d)
        
        # Target info positioning
        if base.mouseWatcherNode.hasMouse():
            if self.target_info_node != None:
                mpos = base.mouseWatcherNode.getMouse()
                r2d = Point3(mpos.getX(), 0, mpos.getY())
                a2d = aspect2d.getRelativePoint(render2d, r2d)
                self.target_info_node.setPos(a2d + Point3(0, 0, 0.08))
        return task.cont
    
    def pickerTask(self, task):
        if self.parent._anim_in_process:
            self.hovered_unit_id = None
            self.hovered_tile = None
            self.hovered_compass_tile = None
            return task.cont
        
        if self.parent.interface.hovered_gui != None:
            if self.hovered_unit_id != None:
                self.parent.sgm.unit_np_dict[int(self.hovered_unit_id)].unmarkHovered()
                self.hovered_unit_id = None
            if self.hovered_tile != None:
                self.hovered_tile.setColor(1, 1, 1)
                self.hovered_tile.setScale(0.05)                
                self.color_scale_parallel.pause()
            if self.hovered_compass_tile != None:
                self.hovered_compass_tile.setColor(1, 1, 1)
                self.hovered_compass_tile.setScale(0.05)                
                self.color_scale_parallel.pause()
            return task.cont
        
        min_distance = 0.5
        min_unit_id = None
        min_tile = None
        min_compass_tile = None
        if base.mouseWatcherNode.hasMouse():
            mpos = base.mouseWatcherNode.getMouse()
            r2d = Point3(mpos.getX(), 0, mpos.getY())
            a2d = aspect2d.getRelativePoint(render2d, r2d)
            self.mouse_node.setPos(a2d)
            
            # At the end of all this we have:
            # - min_distance to a unit or a movement node, IF this distance is lower than 0.5 which is set at the beginning
            # - min_unit_id - ID of unit which is closest to the mouse, or None if there is a movement tile closer, or if everything is further than 0.5
            # - min_tile - nodepath of the movement tile closest to the mouse, or None if there is a unit closer, or if evertythin is further than 0.5
            if self.turn_node.getTag('show') == '1':
                # Get 2d coordinates for every compass node
                for tile in self.turn_np_list:
                    # We cannot do nodepath.getDistance() because tiles are reparented to self.turn_node and are in different coord space than mouse node
                    # So we do simple vector math to get distance
                    d = Vec3(self.mouse_node.getPos() - tile.getPos()).length()
                    if d < min_distance:
                        min_distance = d
                        min_unit_id = None
                        min_tile = None
                        min_compass_tile = tile
            else:
                # Get 2d coordinates of all units
                for unit_id in self.parent.sgm.unit_np_dict:
                    if self.parent.isThisMyUnit(unit_id):
                        u = self.parent.sgm.unit_np_dict[unit_id]
                        # Calculate distance between every friendly unit and mouse cursor and remember closest unit
                        d = self.mouse_node.getDistance(u.node_2d)
                        if d < min_distance:
                            min_distance = d
                            min_unit_id = unit_id
                    elif self.parent.isThisEnemyUnit(unit_id):
                        u = self.parent.sgm.unit_np_dict[unit_id]
                        # Calculate distance between every enemy unit and mouse cursor and remember closest unit
                        d = self.mouse_node.getDistance(u.node_2d)
                        # To target enemy unit, distance has to be even smaller than needed for regular selection/movement
                        if d < min_distance and d < 0.1:
                            min_distance = d
                            min_unit_id = unit_id
            
                # Get 2d coordinates for every movement node of the selected unit
                for tile in self.move_np_list:
                    # We cannot do nodepath.getDistance() because tiles are reparented to self.move_node and are in different coord space than mouse node
                    # So we do simple vector math to get distance
                    d = Vec3(self.mouse_node.getPos() - tile.getPos()).length()
                    if d < min_distance:
                        min_distance = d
                        min_unit_id = None
                        min_tile = tile
            
            
        # If a unit is the closest to the mouse:
        # - hide movement nodes (Incubation style!)
        # - unmark last hovered unit
        # - unmark last hovered tile
        # - mark new hovered unit
        # TODO: ogs: potencijalna optimizacija da se provjeri da li je self.hovered_unit_id = min_unit_id, tada ne treba unmark+mark
        if min_compass_tile != None:
            if self.hovered_tile != None:
                self.hovered_tile.setColor(1, 1, 1)
                self.hovered_tile.setScale(0.05)
                self.color_scale_parallel.pause()
                self.hovered_tile = None
            if min_compass_tile != self.hovered_compass_tile:
                if self.hovered_compass_tile != None:
                    self.hovered_compass_tile.setColor(1, 1, 1)
                    self.hovered_compass_tile.setScale(0.05)
                    self.color_scale_parallel.pause()
                min_compass_tile.setColor(1, 0, 0)
                s1 = Sequence(LerpColorInterval(min_compass_tile, 0.5, (1, 1, 0, 1))
                             ,LerpColorInterval(min_compass_tile, 0.5, (1, 0, 0, 1)))
                s2 = Sequence(LerpScaleInterval(min_compass_tile, 0.5, (0.1))
                             ,LerpScaleInterval(min_compass_tile, 0.5, (0.05)))
                self.color_scale_parallel = Parallel(s1, s2)
                self.color_scale_parallel.loop()
            self.hovered_compass_tile = min_compass_tile
        elif min_unit_id != None:
            self.move_node.detachNode() 
            if min_unit_id != self.hovered_unit_id and self.hovered_unit_id != None:
                if self.parent.sgm.unit_np_dict.has_key(int(self.hovered_unit_id)):
                    self.parent.sgm.unit_np_dict[int(self.hovered_unit_id)].unmarkHovered()
            self.parent.sgm.unit_np_dict[int(min_unit_id)].markHovered()
            if self.hovered_tile != None:
                self.hovered_tile.setColor(1, 1, 1)
                self.hovered_tile.setScale(0.05)   
                self.color_scale_parallel.pause()
                self.hovered_tile = None
            self.hovered_unit_id = min_unit_id
        # If a movement tile is closest to the mouse:
        # - unmark last hovered unit
        # - unmark last marked tile
        # - show movement nodes (Incubation style!)        
        # - mark new hovered tile
        elif min_tile != None:
            if self.hovered_unit_id != None:
                self.parent.sgm.unit_np_dict[int(self.hovered_unit_id)].unmarkHovered() 
                self.hovered_unit_id = None         
            if min_tile != self.hovered_tile:
                self.move_node.reparentTo(aspect2d)
                if self.hovered_tile != None:
                    self.hovered_tile.setColor(1, 1, 1)
                    self.hovered_tile.setScale(0.05)
                    self.color_scale_parallel.pause()
                min_tile.setColor(1, 0, 0)
                s1 = Sequence(LerpColorInterval(min_tile, 0.5, (1, 1, 0, 1))
                             ,LerpColorInterval(min_tile, 0.5, (1, 0, 0, 1)))
                s2 = Sequence(LerpScaleInterval(min_tile, 0.5, (0.1))
                             ,LerpScaleInterval(min_tile, 0.5, (0.05)))
                self.color_scale_parallel = Parallel(s1, s2)
                self.color_scale_parallel.loop()
            self.hovered_tile = min_tile 
        # If neither any of the units nor any of the movement tiles is closer than 0.5:
        # - unmark last hovered unit
        # - unmark last hovered tile
        else:
            if self.hovered_unit_id != None:
                self.parent.sgm.unit_np_dict[int(self.hovered_unit_id)].unmarkHovered()
                self.hovered_unit_id = None
            if self.hovered_tile != None:
                self.hovered_tile.setColor(1, 1, 1)
                self.hovered_tile.setScale(0.05)                
                self.color_scale_parallel.pause()
                self.hovered_tile = None   
            if self.hovered_compass_tile != None:
                self.hovered_compass_tile.setColor(1, 1, 1)
                self.hovered_compass_tile.setScale(0.05)                
                self.color_scale_parallel.pause()
                self.hovered_compass_tile = None         
        return task.cont
    
    
